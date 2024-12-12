import streamlit as st
import os
import tempfile
from dependency_analyzer import analyze_dependencies
from docker_builder import DockerImageBuilder

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
            
            # Docker Image Generation
            st.subheader("Docker Image Generation")
            if st.button("Generate Docker Image"):
                with st.spinner("Building Docker Image..."):
                    builder = DockerImageBuilder(
                        dependencies['package_requirements'], 
                        temp_file_path
                    )
                    image, logs = builder.build_image()
                    
                    if image:
                        output_path = os.path.join(
                            tempfile.gettempdir(), 
                            'airseal_image.tar'
                        )
                        builder.save_image(image, output_path)
                        
                        st.success("Docker Image Generated Successfully!")
                        st.download_button(
                            label="Download Docker Image",
                            data=open(output_path, 'rb'),
                            file_name='airseal_image.tar',
                            mime='application/x-tar'
                        )
                    else:
                        st.error("Failed to build Docker image")
        
        except Exception as e:
            st.error(f"Error processing file: {e}")
        
        # Clean up temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    main()
