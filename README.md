# AirSeal
Automated Airgapping Dependency Packaging Tool

- Currently Supports Python
- Extending to other languages soon


Project Setup and Installation
Prerequisites

Python 3.9+
Docker
pip
git

Clone the Repository
bashCopygit clone https://github.com/harshadindigal/AirSeal
Create Virtual Environment
bashCopypython3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install Dependencies
bashCopypip install -r requirements.txt
Environment Setup
Create a .env file in the project root with the following content:
CopyDOCKER_BUILD_DIR=/path/to/temporary/build/directory
Running the Application
Start Streamlit App
bashCopystreamlit run app.py
Development Scripts

analyze_dependencies.py: Standalone dependency analysis script
docker_builder.py: Docker image generation utility
requirements_generator.py: Dependency extraction tool

Usage Workflow

Upload your Python file
View detected dependencies
Generate Docker image
Download or directly use the generated image

Troubleshooting

Ensure Docker is running
Check console output for specific error messages
Verify Python and dependency versions
