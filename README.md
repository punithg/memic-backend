# memic-backend

## FastAPI Backend Setup (Python 3.14)

1. **Install Python 3.14**
	Download and install Python 3.14 from [python.org](https://www.python.org/downloads/).

2. **Create and activate a virtual environment**
	```bash
	python3.14 -m venv venv
	source venv/bin/activate
	```

3. **Install FastAPI and Uvicorn**
	```bash
	pip install fastapi uvicorn
	```

4. **Create a simple FastAPI app**
	Save the following to `main.py`:
	```python
	from fastapi import FastAPI

	app = FastAPI()

	@app.get("/")
	def read_root():
		 return {"Hello": "World"}
	```

5. **Run the FastAPI server**
	```bash
	uvicorn main:app --reload
	```

6. **Access the API**
	Open [http://localhost:8000](http://localhost:8000) in your browser.
