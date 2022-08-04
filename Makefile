run:
	py EQValet.py

venv:
	python -m venv .venv

setup: requirements.txt
	pip install -r requirements.txt

exe:
	pyinstaller --onefile --icon data/icons/diamond.ico EQValet.py

#zip:
#	cp DeathLoopVaccine.ini.example dist
#	cd dist && zip DeathLoopVaccine.zip DeathLoopVaccine.exe DeathLoopVaccine.ini.example
#
#clean:
#	rm dist/DeathLoopVaccine.exe
#	rm dist/DeathLoopVaccine.ini.example
#	rm dist/DeathLoopVaccine.zip
#	rm build/DeathLoopVaccine/*.*
#	rmdir build/DeathLoopVaccine
#



