# Requirements

- GitHub
- Python (Versions less than 3.14)
- Azure account with Blob Storage, 

# Instructions

1. Clone the Git repo to your local machine
2. Run `pip install -r requirements_openai_current.txt`.
3. Go to the .env file and update your credentials.
4. Download the Kubernetes documentation
5. From `notebooks`, update the `integrated_vectorization_of_kubernetes_documentation.ipynb` notebook with the file path to your K. docs.
6. From `app`, run `python app.py`.
   a. If at anytime you run into a module not found error, run `pip install <module>`. 
   The requirements.txt might contain versions of modules that are outdated.
8. To begin testing the chatbot, start index.html
