import setuptools

setuptools.setup(
    name="streamlit_folium",
    version="0.18.0",
    author="Erik Jensen",
    description="Render Folium objects in Streamlit",
    long_description="",
    long_description_content_type="text/plain",
    url="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.8",
    install_requires=["streamlit>=1.13.0", "folium>=0.13,!=0.15.0", "jinja2", "branca"],
)