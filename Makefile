

flake: .env ./.env/bin/flake8
	# we fix later :P
	./.env/bin/flake8  --ignore=E303,E251,E201,E202,E265,E501  core/bot.py
	

./.env/bin/flake8:
	.env/bin/pip install flake8
.env:
	virtualenv .env
	.env/bin/pip install --upgrade pip
	.env/bin/pip install -r requirements.txt


run: .env
	# Make sure SLACKTOKEN is set
	test -n "$$SLACKTOKEN"
	SLACKBOT=1 ./.env/bin/python core/bot.py sample.config
