:: Install requirements for this program
python -m pip install --upgrade pip --user
python -m pip install --upgrade pipreqs --user
pipreqs ./
python -m pip install -r requirements.txt
del requirements.txt
python -m pip install --upgrade lxml

