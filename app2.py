from h2o_wave import main, app, Q, ui
import os
import tempfile
import base64
import json
from dependency_analyzer import analyze_dependencies
from docker_builder import DockerImageBuilder

async def init(q: Q):
    """Initialize the app state."""
    q.client.initialized = False
    q.client.temp_file_path = None
    q.client.dependencies = None
    q.client.error = None

async def render_page(q: Q):
    """Render the main page layout."""
    # Clear the page
    q.page['meta'] = ui.meta_card(box='', title='AirSeal - Python Dependency Packager')
    
    # Main content card with upload form
    q.page['form'] = ui.form_card(
        box='1 1 -1 -1',
        items=[
            ui.text_xl('AirSeal - Python Dependency Packager'),
            ui.file_upload(
                name='python_file',
                label='Upload Python File',
                multiple=False,
                file_extensions=['py'],
                tooltip='Upload a Python file to analyze its dependencies',
            ),
        ]
    )

    # Show dependency analysis results if available
    if hasattr(q.client, 'dependencies') and q.client.dependencies:
        q.page['analysis'] = ui.form_card(
            box='1 2 -1 -1',
            items=[
                ui.text_xl('Dependency Analysis'),
                ui.text('### Direct Imports'),
                ui.text(f'{json.dumps(q.client.dependencies.get("direct_imports", {}), indent=2)}'),
                ui.text('### Package Requirements'),
                ui.text(f'{json.dumps(q.client.dependencies.get("package_requirements", {}), indent=2)}'),
                ui.text('### Installed Versions'),
                ui.text(f'{json.dumps(q.client.dependencies.get("installed_versions", {}), indent=2)}'),
                ui.button(name='generate_docker_image', label='Generate Docker Image', primary=True),
            ]
        )

    # Show Docker generation output if available
    if hasattr(q.client, 'docker_output') and q.client.docker_output:
        docker_items = [
            ui.text_xl('Docker Image Generation'),
            ui.text(str(q.client.docker_output))  # Convert to string explicitly
        ]
        
        # Add download link if available
        if hasattr(q.client, 'docker_download_url') and q.client.docker_download_url:
            docker_items.extend([
                ui.link(
                    label='Download Docker Image',
                    path=q.client.docker_download_url,
                    download=True
                ),
                ui.text('### How to use the Docker image:'),
                ui.text('''1. Download the .img file
2. Load the image into Docker:
   docker load -i airseal_image.img
3. Run the container:
   docker run airseal-app:latest''')
            ])
        
        q.page['docker'] = ui.form_card(
            box='1 3 -1 -1',
            items=docker_items
        )

    # Show error if any
    if hasattr(q.client, 'error') and q.client.error:
        q.page['error'] = ui.form_card(
            box='1 4 -1 -1',
            items=[
                ui.text_l('Error'),
                ui.text(str(q.client.error)),  # Convert to string explicitly
            ]
        )

async def handle_file_upload(q: Q):
    """Handle file upload and dependency analysis."""
    if q.args.python_file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
                uploaded_file = q.args.python_file[0]
                
                # Handle base64 encoded content
                if ',' in uploaded_file:
                    content = uploaded_file.split(',', 1)[1]
                    decoded_content = base64.b64decode(content).decode('utf-8')
                else:
                    decoded_content = uploaded_file
                
                temp_file.write(decoded_content.encode('utf-8'))
                q.client.temp_file_path = temp_file.name
                
                # Analyze dependencies
                dependencies = analyze_dependencies(temp_file.name)
                if dependencies:
                    q.client.dependencies = dependencies
                else:
                    q.client.dependencies = {
                        "direct_imports": {},
                        "package_requirements": {},
                        "installed_versions": {}
                    }
                
        except Exception as e:
            q.client.error = str(e)
            q.client.dependencies = None

async def handle_docker_generation(q: Q):
    """Handle Docker image generation."""
    try:
        if not hasattr(q.client, 'temp_file_path') or not os.path.exists(q.client.temp_file_path):
            raise FileNotFoundError("Uploaded file not found. Please upload the file again.")

        if not hasattr(q.client, 'dependencies') or not q.client.dependencies:
            raise ValueError("No dependencies found. Please upload and analyze the file first.")

        # Build Docker image with positional arguments instead of keyword arguments
        builder = DockerImageBuilder(
            q.client.dependencies['package_requirements'],
            q.client.temp_file_path
        )
        output_path = builder.build_image()

        if output_path and os.path.exists(output_path):
            # Calculate image size
            image_size = os.path.getsize(output_path) / (1024 * 1024)
            
            # Upload file to get download URL
            download_url, = await q.site.upload([output_path])
            
            q.client.docker_output = f"Docker Image Generated Successfully!\nImage size: {image_size:.2f} MB"
            q.client.docker_download_url = download_url
        else:
            raise ValueError("Failed to generate Docker image output")

    except Exception as e:
        print(f"Docker generation error: {str(e)}")  # Debug print
        q.client.error = f"Failed to build Docker image: {str(e)}"

@app('/')
async def serve(q: Q):
    """Main entry point for the app."""
    if not q.client.initialized:
        await init(q)
        q.client.initialized = True

    if q.args.python_file:
        await handle_file_upload(q)
    elif q.args.generate_docker_image:
        await handle_docker_generation(q)

    await render_page(q)
    await q.page.save()
