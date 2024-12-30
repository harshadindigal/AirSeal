AirSeal
Automated Airgapping Dependency Packaging Tool
Easily package your Python dependencies into a Docker image for secure, airgapped environments.

Features
Currently Supports: Python
Coming Soon: Support for additional programming languages
🚀 Quick Start
Clone the Repository

bash
Copy code
git clone https://github.com/harshadindigal/AirSeal
Set Up Your Virtual Environment

For macOS/Linux:
bash
Copy code
python3 -m venv venv
source venv/bin/activate
For Windows:
bash
Copy code
python -m venv venv
venv\Scripts\activate
Install Dependencies

bash
Copy code
pip install -r requirements.txt
Configure Environment
Create a .env file in the project root and add:

bash
Copy code
DOCKER_BUILD_DIR=/path/to/temporary/build/directory
Run the Application
Start the Streamlit app with:

bash
Copy code
streamlit run app.py
🛠 Development Scripts
analyze_dependencies.py: Analyze and list project dependencies.
docker_builder.py: Generate a Docker image with your dependencies.
requirements_generator.py: Extract and manage dependencies.
📦 Usage Workflow
Upload your Python file
View detected dependencies
Generate Docker image
Download or use the generated Docker image
⚠️ Troubleshooting
Docker Issues: Ensure Docker is running before executing commands.
Python Version: Verify Python version 3.9+ is installed.
Dependency Problems: Check the console output for any specific error messages related to dependencies or environment setup.
📋 Prerequisites
Python 3.9+
Docker
pip
git

