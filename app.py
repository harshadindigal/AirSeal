import streamlit as st
import os
import tempfile
import subprocess
from docker_builder import DockerBuilder
from dependency_analyzer import DependencyAnalyzer

st.title("AirSeal - Automated Dependency Analysis and Docker Image Builder")

uploaded_file = st.file_uploader("Choose a file", type=['py', 'java', 'js', 'cpp', 'go', 'rs'])

if uploaded_file is not None:
    # Display file details
    file_details = {
        "Filename": uploaded_file.name,
        "File size": uploaded_file.size,
        "File type": uploaded_file.type
    }
    st.write(file_details)
    
    if st.button('Build Docker Image'):
        with st.spinner('Building Docker image...'):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    content = uploaded_file.read()
                    tmp_file.write(content)
                    tmp_path = tmp_file.name

                # Analyze dependencies first
                analyzer = DependencyAnalyzer()
                dependencies = analyzer.analyze(tmp_path)
                
                # Show dependencies
                st.subheader("Dependencies Found:")
                for dep in dependencies:
                    st.write(f"- {dep.type}: {dep.name} {dep.version if dep.version else ''}")

                # Build Docker image
                builder = DockerBuilder(tmp_path)
                image_name = builder.build()
                
                if image_name:
                    # Save the Docker image as an img file
                    img_path = os.path.join(tempfile.gettempdir(), f"{image_name.replace(':', '_')}.img")
                    subprocess.run(['docker', 'save', image_name], stdout=open(img_path, 'wb'), check=True)
                    
                    # Provide download button
                    with open(img_path, 'rb') as f:
                        st.success(f"Docker image built successfully!")
                        st.download_button(
                            label="Download Docker Image",
                            data=f,
                            file_name=f"{image_name.replace(':', '_')}.img",
                            mime="application/octet-stream"
                        )
                        
                    # Show docker run command
                    st.code(f"# After downloading, load the image with:\ndocker load < {image_name.replace(':', '_')}.img\n\n# Then run it with:\ndocker run {image_name}")
                    
                    # Cleanup img file
                    os.unlink(img_path)
                else:
                    st.error("Failed to build Docker image")
                    
                # Cleanup
                builder.cleanup()
                os.unlink(tmp_path)
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("""
### Supported Languages:
- Python (.py)
- Java (.java)
- JavaScript (.js)
- C++ (.cpp)
- Go (.go)
- Rust (.rs)

Upload your code file and click 'Build Docker Image' to create a Docker image.
""")