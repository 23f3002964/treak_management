import os
from application import create_app

app = create_app()

if __name__ == '__main__':
    # Run application on port 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
