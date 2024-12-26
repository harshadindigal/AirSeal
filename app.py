import streamlit as st
import os
import tempfile
from dependency_analyzer import analyze_dependencies
from docker_builder import DockerImageBuilder
import subprocess   

def main():
    st.title("AirSeal - Python Dependency Packager")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Python File", 
        type=['py'], 
        help="Upload a Python file to analyze its dependencies"
    )
    
    if uploaded_file is not None:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name
        
        # Analyze dependencies
        st.subheader("Dependency Analysis")
        try:
            dependencies = analyze_dependencies(temp_file_path)
            
            st.write("### Direct Imports")
            st.json(dependencies['direct_imports'])
            
            st.write("### Package Requirements")
            st.json(dependencies['package_requirements'])
            
            st.write("### Installed Versions")
            st.json(dependencies['installed_versions'])
            
            # Docker Image Generation
            st.subheader("Docker Image Generation")
            if st.button("Generate Docker Image"):
                with st.spinner("Building Docker Image..."):
                    try:
                        builder = DockerImageBuilder(
                            dependencies['package_requirements'], 
                            temp_file_path
                        )
                        output_path = builder.build_image()
                        
                        if output_path and os.path.exists(output_path):
                            st.success("Docker Image Generated Successfully!")
                            
                            # Show image information
                            image_size = os.path.getsize(output_path) / (1024 * 1024)  # Convert to MB
                            st.info(f"Image size: {image_size:.2f} MB")
                            
                            # Add download button
                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    label="Download Docker Image (.img)",
                                    data=f,
                                    file_name='airseal_image.img',
                                    mime='application/octet-stream'
                                )
                            
                            # Add usage instructions
                            st.markdown("""
                            ### How to use the Docker image:
                            1. Download the .img file
                            2. Load the image into Docker:
                            ```bash
                            docker load -i airseal_image.img
                            ```
                            3. Run the container:
                            ```bash
                            docker run airseal-app:latest
                            ```
                            """)
                    except Exception as e:
                        st.error(f"Failed to build Docker image: {str(e)}")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
        
        # Clean up temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
