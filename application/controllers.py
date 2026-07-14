import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from application import db
from application.models import User, Trek, Booking
from werkzeug.security import generate_password_hash, check_password_hash

main_bp = Blueprint('main', __name__)

# -----------------------------------------------------------------------------
# Security & Access Control Decorators
# -----------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
        
        # Verify user still exists and is not blacklisted
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('main.login'))
        
        if user.status == 'blacklisted':
            session.clear()
            flash('Your account has been blacklisted. Access denied.', 'danger')
            return redirect(url_for('main.login'))
            
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
            
            # Additional check for staff approval
            if session.get('role') == 'staff':
                user = User.query.get(session['user_id'])
                if user.status == 'pending':
                    flash('Your staff account is pending administrator approval.', 'warning')
                    return redirect(url_for('main.staff_pending_dashboard'))
                elif user.status != 'approved':
                    flash('Access Denied. Your account status is not approved.', 'danger')
                    return redirect(url_for('main.logout'))
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@main_bp.route('/')
def index():
    # Fetch some open treks for landing page
    open_treks = Trek.query.filter_by(status='Open').limit(3).all()
    return render_template('index.html', open_treks=open_treks)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        elif role == 'staff':
            return redirect(url_for('main.staff_dashboard'))
        else:
            return redirect(url_for('main.trekker_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if user.status == 'blacklisted':
                flash('Your account has been blacklisted by the Administrator.', 'danger')
                return render_template('login.html')

            # Staff pending approval are allowed to log in but will be routed to pending dashboard
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['name'] = user.name

            if user.role == 'admin':
                flash(f'Welcome back Admin, {user.name}!', 'success')
                return redirect(url_for('main.admin_dashboard'))
            elif user.role == 'staff':
                if user.status == 'pending':
                    flash('Your account is pending admin approval.', 'warning')
                    return redirect(url_for('main.staff_pending_dashboard'))
                flash(f'Welcome, {user.name} (Trek Staff)!', 'success')
                return redirect(url_for('main.staff_dashboard'))
            else:
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(url_for('main.trekker_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        contact_details = request.form.get('contact_details', '').strip()
        role = request.form.get('role', 'trekker')

        if not username or not password or not name or not contact_details:
            flash('All fields are required.', 'warning')
            return render_template('register.html')

        if role not in ['trekker', 'staff']:
            flash('Invalid role selected.', 'danger')
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username is already taken. Please choose another.', 'warning')
            return render_template('register.html')

        status = 'pending' if role == 'staff' else 'active'
        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            password_hash=hashed_password,
            name=name,
            contact_details=contact_details,
            role=role,
            status=status
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            if role == 'staff':
                flash('Registration successful! Please wait for admin approval before logging in.', 'success')
            else:
                flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('register.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

# -----------------------------------------------------------------------------
# Staff Pending Approval Dashboard Route
# -----------------------------------------------------------------------------
@main_bp.route('/staff/pending')
@login_required
def staff_pending_dashboard():
    user = User.query.get(session['user_id'])
    if not user or user.role != 'staff':
        return redirect(url_for('main.index'))
    if user.status == 'approved':
        return redirect(url_for('main.staff_dashboard'))
    return render_template('staff/pending.html')

# -----------------------------------------------------------------------------
# Admin Functionalities (Role: admin)
# -----------------------------------------------------------------------------

@main_bp.route('/admin/dashboard')
@role_required(['admin'])
def admin_dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    pending_staff = User.query.filter_by(role='staff', status='pending').all()
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
        recent_bookings=recent_bookings
    )

@main_bp.route('/admin/treks', methods=['GET', 'POST'])
@role_required(['admin'])
def admin_treks():
    if request.method == 'POST':
        # Create a new trek
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty')
        duration = request.form.get('duration')
        total_slots = request.form.get('total_slots')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        description = request.form.get('description', '').strip()
        price = request.form.get('price', 0.0)

        # Basic validations
        if not name or not location or not difficulty or not duration or not total_slots or not start_date_str or not end_date_str:
            flash('All required fields must be completed.', 'warning')
            return redirect(url_for('main.admin_treks'))

        try:
            duration = int(duration)
            total_slots = int(total_slots)
            price = float(price)
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid numeric inputs or dates.', 'warning')
            return redirect(url_for('main.admin_treks'))

        if end_date < start_date:
            flash('End date cannot be before start date.', 'warning')
            return redirect(url_for('main.admin_treks'))

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=duration,
            total_slots=total_slots,
            available_slots=total_slots, # Initially all slots are available
            status='Approved', # Default is Approved, Staff can set it to Open
            start_date=start_date,
            end_date=end_date,
            description=description,
            price=price
        )

        db.session.add(new_trek)
        db.session.commit()
        flash('New trek route added successfully!', 'success')
        return redirect(url_for('main.admin_treks'))

    # GET requests - list all treks and staff list for assign dropdowns
    search_query = request.args.get('search', '').strip()
    difficulty_filter = request.args.get('difficulty', '')
    status_filter = request.args.get('status', '')

    query = Trek.query
    if search_query:
        query = query.filter((Trek.name.like(f'%{search_query}%')) | (Trek.location.like(f'%{search_query}%')) | (Trek.id == search_query))
    if difficulty_filter:
        query = query.filter_by(difficulty=difficulty_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)

    treks = query.all()
    approved_staff = User.query.filter_by(role='staff', status='approved').all()

    return render_template('admin/treks.html', treks=treks, approved_staff=approved_staff, search=search_query, difficulty=difficulty_filter, status=status_filter)

@main_bp.route('/admin/treks/edit/<int:trek_id>', methods=['POST'])
@role_required(['admin'])
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    name = request.form.get('name', '').strip()
    location = request.form.get('location', '').strip()
    difficulty = request.form.get('difficulty')
    duration = request.form.get('duration')
    total_slots_str = request.form.get('total_slots')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    description = request.form.get('description', '').strip()
    price = request.form.get('price', 0.0)
    status = request.form.get('status')

    if not name or not location or not difficulty or not duration or not total_slots_str or not start_date_str or not end_date_str:
        flash('All required fields must be completed.', 'warning')
        return redirect(url_for('main.admin_treks'))

    try:
        duration = int(duration)
        new_total_slots = int(total_slots_str)
        price = float(price)
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid numeric inputs or dates.', 'warning')
        return redirect(url_for('main.admin_treks'))

    if end_date < start_date:
        flash('End date cannot be before start date.', 'warning')
        return redirect(url_for('main.admin_treks'))

    # Calculate actual booked slots from active bookings to adjust available slots
    booked_slots = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
    if new_total_slots < booked_slots:
        flash(f'Cannot set total slots to {new_total_slots} because {booked_slots} slots are already booked.', 'danger')
        return redirect(url_for('main.admin_treks'))

    trek.name = name
    trek.location = location
    trek.difficulty = difficulty
    trek.duration = duration
    trek.total_slots = new_total_slots
    trek.available_slots = new_total_slots - booked_slots
    trek.start_date = start_date
    trek.end_date = end_date
    trek.description = description
    trek.price = price
    if status:
        trek.status = status

    db.session.commit()
    flash(f'Trek "{trek.name}" updated successfully!', 'success')
    return redirect(url_for('main.admin_treks'))

@main_bp.route('/admin/treks/delete/<int:trek_id>', methods=['POST'])
@role_required(['admin'])
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    name = trek.name
    try:
        db.session.delete(trek)
        db.session.commit()
        flash(f'Trek "{name}" removed successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash(f'Cannot delete trek "{name}" as it has linked bookings. Try changing its status to Closed instead.', 'danger')
    return redirect(url_for('main.admin_treks'))

@main_bp.route('/admin/treks/assign/<int:trek_id>', methods=['POST'])
@role_required(['admin'])
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_id_str = request.form.get('staff_id')

    if not staff_id_str:
        trek.assigned_staff_id = None
        db.session.commit()
        flash('Removed assigned staff from the trek.', 'info')
        return redirect(url_for('main.admin_treks'))

    try:
        staff_id = int(staff_id_str)
        staff = User.query.filter_by(id=staff_id, role='staff', status='approved').first()
        if not staff:
            flash('Invalid or unapproved staff selected.', 'danger')
            return redirect(url_for('main.admin_treks'))
        
        trek.assigned_staff_id = staff_id
        db.session.commit()
        flash(f'Assigned guide {staff.name} to {trek.name}.', 'success')
    except ValueError:
        flash('Invalid request parameters.', 'danger')
        
    return redirect(url_for('main.admin_treks'))

@main_bp.route('/admin/staff', methods=['GET', 'POST'])
@role_required(['admin'])
def admin_staff():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    query = User.query.filter_by(role='staff')
    if search_query:
        query = query.filter((User.name.like(f'%{search_query}%')) | (User.username.like(f'%{search_query}%')) | (User.id == search_query))
    if status_filter:
        query = query.filter_by(status=status_filter)

    staff_members = query.all()
    return render_template('admin/staff.html', staff=staff_members, search=search_query, status=status_filter)

@main_bp.route('/admin/staff/action/<int:staff_id>/<string:action>', methods=['POST'])
@role_required(['admin'])
def staff_action(staff_id, action):
    staff = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    
    if action == 'approve':
        staff.status = 'approved'
        flash(f'Staff member {staff.name} approved successfully.', 'success')
    elif action == 'blacklist':
        staff.status = 'blacklisted'
        flash(f'Staff member {staff.name} has been blacklisted.', 'warning')
    elif action == 'unblacklist':
        staff.status = 'approved'
        flash(f'Staff member {staff.name} blacklist removed.', 'success')
    else:
        flash('Invalid staff action requested.', 'danger')

    db.session.commit()
    return redirect(url_for('main.admin_staff'))

@main_bp.route('/admin/users')
@role_required(['admin'])
def admin_users():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    query = User.query.filter_by(role='trekker')
    if search_query:
        query = query.filter((User.name.like(f'%{search_query}%')) | (User.username.like(f'%{search_query}%')) | (User.id == search_query))
    if status_filter:
        query = query.filter_by(status=status_filter)

    users_list = query.all()
    return render_template('admin/users.html', users=users_list, search=search_query, status=status_filter)

@main_bp.route('/admin/users/action/<int:user_id>/<string:action>', methods=['POST'])
@role_required(['admin'])
def user_action(user_id, action):
    user = User.query.filter_by(id=user_id, role='trekker').first_or_404()
    
    if action == 'blacklist':
        user.status = 'blacklisted'
        flash(f'Trekker {user.name} has been blacklisted.', 'warning')
    elif action == 'unblacklist':
        user.status = 'active'
        flash(f'Trekker {user.name} blacklist removed.', 'success')
    else:
        flash('Invalid user action requested.', 'danger')

    db.session.commit()
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/bookings')
@role_required(['admin'])
def admin_bookings():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')

    query = Booking.query
    if search_query:
        query = query.join(Trek).join(User, Booking.user_id == User.id).filter(
            (Trek.name.like(f'%{search_query}%')) | 
            (User.name.like(f'%{search_query}%')) | 
            (Booking.id == search_query)
        )
    if status_filter:
        query = query.filter(Booking.status == status_filter)

    bookings_list = query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings_list, search=search_query, status=status_filter)

# -----------------------------------------------------------------------------
# Trek Staff Functionalities (Role: staff)
# -----------------------------------------------------------------------------

@main_bp.route('/staff/dashboard')
@role_required(['staff'])
def staff_dashboard():
    staff_id = session['user_id']
    # Show treks assigned to this guide
    assigned_treks = Trek.query.filter_by(assigned_staff_id=staff_id).all()
    return render_template('staff/dashboard.html', treks=assigned_treks)

@main_bp.route('/staff/trek/<int:trek_id>', methods=['GET', 'POST'])
@role_required(['staff'])
def staff_trek_detail(trek_id):
    staff_id = session['user_id']
    trek = Trek.query.filter_by(id=trek_id, assigned_staff_id=staff_id).first_or_404()

    if request.method == 'POST':
        # Update trek details (available slots and status)
        new_status = request.form.get('status')
        new_slots_str = request.form.get('available_slots')

        if new_status:
            trek.status = new_status

        if new_slots_str is not None:
            try:
                new_slots = int(new_slots_str)
                # Ensure capacity limit is not exceeded by checking active bookings
                booked_slots = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
                if new_slots + booked_slots > trek.total_slots:
                    flash(f'Available slots cannot exceed remaining total capacity. Maximum available: {trek.total_slots - booked_slots}', 'danger')
                    return redirect(url_for('main.staff_trek_detail', trek_id=trek.id))
                if new_slots < 0:
                    flash('Available slots cannot be negative.', 'danger')
                    return redirect(url_for('main.staff_trek_detail', trek_id=trek.id))
                trek.available_slots = new_slots
            except ValueError:
                flash('Available slots must be an integer.', 'warning')
                return redirect(url_for('main.staff_trek_detail', trek_id=trek.id))

        db.session.commit()
        flash('Trek details updated successfully.', 'success')
        return redirect(url_for('main.staff_trek_detail', trek_id=trek.id))

    # GET requests - show details and participant list
    participants = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
    return render_template('staff/trek_detail.html', trek=trek, participants=participants)

# -----------------------------------------------------------------------------
# Trekker / User Functionalities (Role: trekker)
# -----------------------------------------------------------------------------

@main_bp.route('/user/dashboard')
@role_required(['trekker'])
def trekker_dashboard():
    search_query = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    difficulty_filter = request.args.get('difficulty', '')

    query = Trek.query.filter(Trek.status.in_(['Open', 'Approved']))

    if search_query:
        query = query.filter(Trek.name.like(f'%{search_query}%'))
    if location_filter:
        query = query.filter(Trek.location.like(f'%{location_filter}%'))
    if difficulty_filter:
        query = query.filter_by(difficulty=difficulty_filter)

    available_treks = query.all()
    
    # Also fetch the user's upcoming active bookings
    user_id = session['user_id']
    active_bookings = Booking.query.filter_by(user_id=user_id, status='Booked').all()
    booked_trek_ids = [b.trek_id for b in active_bookings]

    return render_template(
        'user/dashboard.html',
        treks=available_treks,
        booked_trek_ids=booked_trek_ids,
        search=search_query,
        location=location_filter,
        difficulty=difficulty_filter
    )

@main_bp.route('/user/book/<int:trek_id>', methods=['POST'])
@role_required(['trekker'])
def book_trek(trek_id):
    user_id = session['user_id']
    trek = Trek.query.get_or_404(trek_id)

    # 1. Allow user to book only if trek status is Open
    if trek.status != 'Open':
        flash('This trek is not open for bookings.', 'danger')
        return redirect(url_for('main.trekker_dashboard'))

    # 2. Prevent overbooking beyond available slots
    if trek.available_slots <= 0:
        flash('Sorry, this trek is fully booked.', 'danger')
        return redirect(url_for('main.trekker_dashboard'))

    # 3. Check if they already have an active booking for this trek
    existing_booking = Booking.query.filter_by(user_id=user_id, trek_id=trek_id, status='Booked').first()
    if existing_booking:
        flash('You have already booked this trek.', 'info')
        return redirect(url_for('main.trekker_dashboard'))

    # 4. Create booking transactionally
    try:
        trek.available_slots -= 1
        
        booking = Booking(
            user_id=user_id,
            trek_id=trek_id,
            status='Booked'
        )
        db.session.add(booking)
        db.session.commit()
        flash(f'Trek "{trek.name}" booked successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Could not complete booking. Please try again.', 'danger')

    return redirect(url_for('main.trekker_dashboard'))

@main_bp.route('/user/cancel_booking/<int:booking_id>', methods=['POST'])
@role_required(['trekker'])
def cancel_booking(booking_id):
    user_id = session['user_id']
    booking = Booking.query.get_or_404(booking_id)

    # Ensure this booking belongs to the logged-in user
    if booking.user_id != user_id:
        flash('Access Denied. You cannot cancel someone else\'s booking.', 'danger')
        return redirect(url_for('main.trekker_history'))

    if booking.status != 'Booked':
        flash('This booking cannot be cancelled (current status: {}).'.format(booking.status), 'warning')
        return redirect(url_for('main.trekker_history'))

    # Check if trek is already completed or past
    trek = booking.trek
    if trek.start_date <= datetime.date.today():
        flash('You cannot cancel a booking on or after the trek start date.', 'danger')
        return redirect(url_for('main.trekker_history'))

    try:
        trek.available_slots += 1
        booking.status = 'Cancelled'
        db.session.commit()
        flash(f'Booking for "{trek.name}" has been cancelled.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Booking cancellation failed.', 'danger')

    return redirect(url_for('main.trekker_history'))

@main_bp.route('/user/history')
@role_required(['trekker'])
def trekker_history():
    user_id = session['user_id']
    bookings_history = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()
    return render_template('user/history.html', bookings=bookings_history)

@main_bp.route('/user/profile', methods=['GET', 'POST'])
@role_required(['trekker'])
def trekker_profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_details = request.form.get('contact_details', '').strip()
        password = request.form.get('password', '')

        if not name or not contact_details:
            flash('Name and contact details are required.', 'warning')
            return render_template('user/profile.html', user=user)

        user.name = name
        user.contact_details = contact_details
        
        if password:
            user.password_hash = generate_password_hash(password)

        db.session.commit()
        # Update name in session
        session['name'] = user.name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('main.trekker_profile'))

    return render_template('user/profile.html', user=user)

# -----------------------------------------------------------------------------
# REST API Endpoints (Return JSON)
# -----------------------------------------------------------------------------

@main_bp.route('/api/treks', methods=['GET'])
def api_treks():
    treks = Trek.query.all()
    return jsonify([t.to_dict() for t in treks])

@main_bp.route('/api/bookings', methods=['GET'])
def api_bookings():
    # Only Admin is allowed to fetch all bookings via API for security
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized access. Admin privileges required.'}), 403
    
    bookings = Booking.query.all()
    return jsonify([b.to_dict() for b in bookings])

@main_bp.route('/api/users', methods=['GET'])
def api_users():
    # Only Admin is allowed to fetch all users via API for security
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized access. Admin privileges required.'}), 403
    
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])
