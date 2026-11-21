import os
import sys

sys.path.insert(0, os.path.abspath("."))
from app.core.security import verify_password
from app.db.session import SessionLocal
from app.modules.users.models import User

s = SessionLocal()
for email in ["admin@mediatehealthcare.com", "manager@mediatehealthcare.com", "mr@mediatehealthcare.com"]:
    u = s.query(User).filter(User.email == email).first()
    if u:
        p_admin = verify_password("Admin@123", u.hashed_password)
        p_mgr = verify_password("Manager@123", u.hashed_password)
        p_mr = verify_password("Mr@123", u.hashed_password)
        print(email, "-> Admin@123:", p_admin, "Manager@123:", p_mgr, "Mr@123:", p_mr, flush=True)
s.close()
