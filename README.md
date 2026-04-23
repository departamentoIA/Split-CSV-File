# Split-CSV-File
Split a big CSV file into many XLSX files of 1 million rows.

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
python main.py Emisor_PME380607P35.csv -o partes -c 1000000
```
## 🎯 Results
For Windows, use a PowerShell terminal to run "main.py", then the folder "partes" is created with the corresponding XLSX files, as shown in Fig. 1. Remember to activate the virtual enviroment.
<img width="1433" height="735" alt="image" src="https://github.com/user-attachments/assets/e5b93b1f-fb36-4f3d-9d5f-5631bdbf558e" />
Fig. 1.

