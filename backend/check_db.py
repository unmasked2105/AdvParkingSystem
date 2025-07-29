from app import app, db, Admin, User, ParkingZone, ParkingSlot

with app.app_context():
    print("Checking database...")
    
    # Check if admin exists
    admin = Admin.query.filter_by(email='admin@admin.com').first()
    if admin:
        print(f"Admin exists: {admin.email} - {admin.fullname}")
    else:
        print(" Admin not found")
    
    # Check if users exist
    users = User.query.all()
    print(f"📊 Total users: {len(users)}")
    
    # Check if parking zones exist
    zones = ParkingZone.query.all()
    print(f"🚗 Total parking zones: {len(zones)}")
    
    # Check if parking slots exist
    slots = ParkingSlot.query.all()
    print(f"🅿️ Total parking slots: {len(slots)}")
    
    print("\nDatabase check complete!") 