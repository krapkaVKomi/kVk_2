from email_validator import validate_email, EmailNotValidError



email = "lg2031832@gmail.com"

try:
  email = validate_email(email).email
except EmailNotValidError as e:
  print(str(e))
