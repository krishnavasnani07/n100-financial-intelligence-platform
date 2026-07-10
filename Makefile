.PHONY: install test run clean

# Default task
all: install

# Install dependencies
install:
	pip install -r requirements.txt

# Run main application
run:
	python main.py

# Run tests
test:
	pytest tests/

# Clean up cache files
clean:
	rmdir /s /q __pycache__ 2>nul || rm -rf __pycache__
	rmdir /s /q src\__pycache__ 2>nul || rm -rf src/__pycache__
	rmdir /s /q src\etl\__pycache__ 2>nul || rm -rf src/etl/__pycache__
	rmdir /s /q src\database\__pycache__ 2>nul || rm -rf src/database/__pycache__
	rmdir /s /q src\utils\__pycache__ 2>nul || rm -rf src/utils/__pycache__
	rmdir /s /q src\validation\__pycache__ 2>nul || rm -rf src/validation/__pycache__
	rmdir /s /q src\config\__pycache__ 2>nul || rm -rf src/config/__pycache__
