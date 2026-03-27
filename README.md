# Split-CSV-File
Split a big CSV file into many parts

## 🚀 How to run locally
1. Clone this repository:
```
git clone https://github.com/departamentoIA/Split-CSV-File.git
```
2. Set virtual environment and install dependencies.

For Windows:
```
python -m venv env
env/Scripts/activate
pip install -r requirements.txt
```
For Linux:
```
python -m venv env && source env/bin/activate && pip install -r requirements.txt
```
3. Run "main.py" using file 'Emisor_PME380607P35.csv':
```
python main.py Emisor_PME380607P35.csv -o partes_csv -c 1000000
```