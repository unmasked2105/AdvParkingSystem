from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash, send_file
from datetime import datetime, timedelta
from models import db, User, ParkingSlot, ParkingZone, Booking, Payment, Admin
from sqlalchemy import or_, func
import qrcode
import io
import base64
import uuid
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'
jwt = JWTManager(app)

# CORS for Vue frontend
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create admin on startup
def create_admin():
    with app.app_context():
        admin = Admin.query.filter_by(email='admin@admin.com').first()
        if not admin:
            admin = Admin(
                email='admin@admin.com',
                password='admin123',
                fullname='Admin',
                address='Admin Address',
                pincode='123456'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created successfully!")

# Create database tables first, then create admin
with app.app_context():
    db.create_all()
    create_admin()

# this is authentication part which is used by us
@app.route('/api/user/register', methods=['POST'])
def api_user_register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    fullname = data.get('fullname')
    address = data.get('address')
    pincode = data.get('pincode')

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 409

    new_user = User(email=email, password=password, fullname=fullname,
                    address=address, pincode=pincode)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

@app.route('/api/admin/register', methods=['POST'])
def api_admin_register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    fullname = data.get('fullname')
    address = data.get('address')
    pincode = data.get('pincode')

    # Check if admin already exists
    existing_admin = Admin.query.filter_by(email=email).first()
    if existing_admin:
        return jsonify({'error': 'Admin already exists'}), 409

    new_admin = Admin(email=email, password=password, fullname=fullname,
                      address=address, pincode=pincode)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({'message': 'Admin registered successfully'})

@app.route('/api/user/login', methods=['POST'])
def api_user_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password).first()
    if user:
        # Convert user.id to string for JWT
        token = create_access_token(identity=str(user.id), additional_claims={'role': 'user'})
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'fullname': user.fullname,
                'address': user.address,
                'pincode': user.pincode
            }
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    try:
        data = request.get_json()
        print("Admin login attempt:", data)  # Debug print
        
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        admin = Admin.query.filter_by(email=email, password=password).first()
        print("Found admin:", admin)  # Debug print
        
        if admin:
            # Convert admin.id to string for JWT
            token = create_access_token(identity=str(admin.id), additional_claims={'role': 'admin'})
            print("Generated token for admin:", admin.id)  # Debug print
            return jsonify({
                'token': token,
                'admin': {
                    'id': admin.id,
                    'email': admin.email,
                    'fullname': admin.fullname
                }
            })
        else:
            print("No admin found with credentials")  # Debug print
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print("Error in admin login:", str(e))  # Debug print
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def api_user_profile():
    user_id = int(get_jwt_identity())  # Convert string to int
    user = User.query.get(user_id)
    if user:
        return jsonify({
            'id': user.id,
            'email': user.email,
            'fullname': user.fullname,
            'address': user.address,
            'pincode': user.pincode
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def api_update_user_profile():
    user_id = int(get_jwt_identity())  # Convert string to int
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    user.fullname = data.get('fullname', user.fullname)
    user.address = data.get('address', user.address)
    user.pincode = data.get('pincode', user.pincode)
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'})

@app.route('/api/admin/profile', methods=['GET'])
@jwt_required()
def api_admin_profile():
    admin_id = int(get_jwt_identity())  # Convert string to int
    admin = Admin.query.get(admin_id)
    if admin:
        return jsonify({
            'id': admin.id,
            'email': admin.email,
            'fullname': admin.fullname
        })
    return jsonify({'error': 'Admin not found'}), 404

# Search endpoints
@app.route('/api/search_slots', methods=['POST'])
@jwt_required()
def api_search_slots():
    data = request.get_json()
    location = data.get('location', '')
    pincode = data.get('pincode', '')
    
    # Start with all parking zones
    query = ParkingZone.query
    
    if location:
        query = query.filter(ParkingZone.name.ilike(f'%{location}%'))
    
    lots = query.all()
    lots_data = []
    
    for lot in lots:
        # Get slots for this lot
        slots_query = ParkingSlot.query.filter_by(zone_id=lot.id)
        
        # Filter by pincode if provided
        if pincode:
            slots_query = slots_query.filter(ParkingSlot.pincode.ilike(f'%{pincode}%'))
        
        available_slots = slots_query.filter_by(is_available=True).all()
        
        # Only include lots that have matching slots
        if available_slots:
            # Get the first slot to get pincode and price
            first_slot = available_slots[0]
            
            lots_data.append({
                'id': lot.id,
                'prime_location_name': lot.name,
                'address': lot.city,
                'pincode': first_slot.pincode,
                'price': first_slot.price_per_hour,
                'number_of_spots': len(available_slots)
            })
    
    return jsonify({'results': lots_data})

@app.route('/api/admin/search', methods=['POST'])
@jwt_required()
def api_admin_search():
    try:
        # Check if user is admin
        admin_id = int(get_jwt_identity())  # Convert string to int
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        search_query = data.get('search_query', '')
        search_type = data.get('search_type', 'all')  # all, users, lots
        filter_type = data.get('filter_type', 'id')  # id, name, email, pincode, address
        
        results = {
            'users': [],
            'lots': []
        }
        
        # Search users by specific filter type
        if search_type in ['all', 'users']:
            users = []
            if search_query:
                if filter_type == 'id' and search_query.isdigit():
                    # Search by ID
                    user_by_id = User.query.filter_by(id=int(search_query)).first()
                    if user_by_id:
                        users.append(user_by_id)
                elif filter_type == 'name':
                    # Search by name
                    users = User.query.filter(User.fullname.ilike(f'%{search_query}%')).all()
                elif filter_type == 'email':
                    # Search by email
                    users = User.query.filter(User.email.ilike(f'%{search_query}%')).all()
                elif filter_type == 'pincode':
                    # Search by pincode
                    users = User.query.filter(User.pincode.ilike(f'%{search_query}%')).all()
                elif filter_type == 'address':
                    # Search by address
                    users = User.query.filter(User.address.ilike(f'%{search_query}%')).all()
                else:
                    # Fallback: search across all fields
                    users = User.query.filter(
                        or_(
                            User.fullname.ilike(f'%{search_query}%'),
                            User.email.ilike(f'%{search_query}%'),
                            User.pincode.ilike(f'%{search_query}%'),
                            User.address.ilike(f'%{search_query}%')
                        )
                    ).all()
            else:
                # If no search query, return all users
                users = User.query.all()
            
            results['users'] = [{
                'id': user.id,
                'email': user.email,
                'fullname': user.fullname,
                'address': user.address,
                'pincode': user.pincode
            } for user in users]
        
        # Search lots by specific filter type
        if search_type in ['all', 'lots']:
            lots = []
            if search_query:
                if filter_type == 'id' and search_query.isdigit():
                    # Search by ID
                    lot_by_id = ParkingZone.query.filter_by(id=int(search_query)).first()
                    if lot_by_id:
                        lots.append(lot_by_id)
                elif filter_type == 'name':
                    # Search by name
                    lots = ParkingZone.query.filter(ParkingZone.name.ilike(f'%{search_query}%')).all()
                elif filter_type == 'email':
                    # Email not applicable for lots, return empty
                    lots = []
                elif filter_type == 'pincode':
                    # Search by pincode (from associated slots)
                    lots = ParkingZone.query.join(ParkingSlot).filter(
                        ParkingSlot.pincode.ilike(f'%{search_query}%')
                    ).distinct().all()
                elif filter_type == 'address':
                    # Search by address (from associated slots)
                    lots = ParkingZone.query.join(ParkingSlot).filter(
                        ParkingSlot.location.ilike(f'%{search_query}%')
                    ).distinct().all()
                else:
                    # Fallback: search across all fields
                    lots = ParkingZone.query.join(ParkingSlot).filter(
                        or_(
                            ParkingZone.name.ilike(f'%{search_query}%'),
                            ParkingZone.city.ilike(f'%{search_query}%'),
                            ParkingSlot.pincode.ilike(f'%{search_query}%'),
                            ParkingSlot.location.ilike(f'%{search_query}%')
                        )
                    ).distinct().all()
            else:
                # If no search query, return all lots
                lots = ParkingZone.query.all()
            
            lots_data = []
            for lot in lots:
                # Get the first slot to get pincode and price
                first_slot = ParkingSlot.query.filter_by(zone_id=lot.id).first()
                pincode = first_slot.pincode if first_slot else 'N/A'
                price = first_slot.price_per_hour if first_slot else 0.0
                
                lots_data.append({
                    'id': lot.id,
                    'prime_location_name': lot.name,
                    'address': lot.city,
                    'pincode': pincode,
                    'price': price,
                    'number_of_spots': len(lot.slots)
                })
            results['lots'] = lots_data
        
        return jsonify(results)
    except Exception as e:
        print("Error in admin search:", str(e))  # Debug print
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/search_user', methods=['POST'])
@jwt_required()
def api_search_user():
    data = request.get_json()
    user_id = data.get('user_id')
    pincode = data.get('pincode')
    
    users = []
    
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        if user:
            users.append(user)
    elif pincode:
        users = User.query.filter(User.pincode.ilike(f'%{pincode}%')).all()
    
    if not users:
        return jsonify({'error': 'No matching users found'}), 404
    
    return jsonify({
        'users': [{
            'id': user.id,
            'email': user.email,
            'fullname': user.fullname,
            'address': user.address,
            'pincode': user.pincode
        } for user in users]
    })

# Admin CRUD for Parking Lots
@app.route('/api/admin/lots', methods=['POST'])
@jwt_required()
def api_create_lot():
    try:
        data = request.get_json()
        print("Received lot data:", data)  # Debug print
        
        name = data.get('name')
        address = data.get('address')
        pincode = data.get('pincode')
        price = data.get('price')
        spots = data.get('spots')

        # Validate required fields
        if not all([name, address, pincode, price, spots]):
            missing_fields = []
            if not name: missing_fields.append('name')
            if not address: missing_fields.append('address')
            if not pincode: missing_fields.append('pincode')
            if not price: missing_fields.append('price')
            if not spots: missing_fields.append('spots')
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Create new parking zone
        new_lot = ParkingZone(name=name, city=address)
        db.session.add(new_lot)
        db.session.flush()  # Get the ID without committing

        # Create parking spots
        for i in range(int(spots)):
            new_slot = ParkingSlot(
                location=address,
                slot_number=f"{name}-{i+1}",
                price_per_hour=float(price),
                pincode=pincode,
                zone_id=new_lot.id
            )
            db.session.add(new_slot)
        
        db.session.commit()
        print(f"Successfully created lot: {new_lot.name} with {spots} spots")  # Debug print
        return jsonify({'message': 'Parking lot created successfully', 'lot_id': new_lot.id})
    except Exception as e:
        db.session.rollback()
        print("Error creating lot:", str(e))  # Debug print
        return jsonify({'error': f'Failed to create lot: {str(e)}'}), 500

@app.route('/api/admin/lots', methods=['GET'])
@jwt_required()
def api_get_lots():
    try:
        lots = ParkingZone.query.all()
        lots_data = []
        for lot in lots:
            # Get the first slot to get pincode and price
            first_slot = ParkingSlot.query.filter_by(zone_id=lot.id).first()
            pincode = first_slot.pincode if first_slot else 'N/A'
            price = first_slot.price_per_hour if first_slot else 0.0
            
            lots_data.append({
                'id': lot.id,
                'prime_location_name': lot.name,
                'address': lot.city,
                'pincode': pincode,
                'price': price,
                'number_of_spots': len(lot.slots)
            })
        return jsonify(lots_data)
    except Exception as e:
        print("Error getting lots:", str(e))  # Debug print
        return jsonify({'error': f'Failed to get lots: {str(e)}'}), 500

@app.route('/api/admin/lots/<int:lot_id>', methods=['PUT'])
@jwt_required()
def api_update_lot(lot_id):
    lot = ParkingZone.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'Lot not found'}), 404
    
    data = request.get_json()
    lot.name = data.get('name', lot.name)
    lot.city = data.get('address', lot.city)
    db.session.commit()
    return jsonify({'message': 'Lot updated successfully'})

@app.route('/api/admin/lots/<int:lot_id>', methods=['DELETE'])
@jwt_required()
def api_delete_lot(lot_id):
    lot = ParkingZone.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'Lot not found'}), 404
    
    # Check if any spots are occupied
    occupied_spots = ParkingSlot.query.filter_by(zone_id=lot_id, is_available=False).count()
    if occupied_spots > 0:
        return jsonify({'error': 'Cannot delete lot with occupied spots'}), 400
    
    # Delete all spots first
    ParkingSlot.query.filter_by(zone_id=lot_id).delete()
    db.session.delete(lot)
    db.session.commit()
    return jsonify({'message': 'Lot deleted successfully'})

@app.route('/api/admin/lots/<int:lot_id>/spots', methods=['GET'])
@jwt_required()
def api_get_lot_spots(lot_id):
    spots = ParkingSlot.query.filter_by(zone_id=lot_id).all()
    return jsonify([{
        'id': spot.id,
        'slot_number': spot.slot_number,
        'is_available': spot.is_available,
        'price_per_hour': spot.price_per_hour,
        'location': spot.location
    } for spot in spots])

# User endpoints
@app.route('/api/user/lots', methods=['GET'])
@jwt_required()
def api_user_lots():
    lots = ParkingZone.query.all()
    lots_data = []
    for lot in lots:
        # Get the first slot to get pincode and price
        first_slot = ParkingSlot.query.filter_by(zone_id=lot.id).first()
        pincode = first_slot.pincode if first_slot else 'N/A'
        price = first_slot.price_per_hour if first_slot else 0.0
        
        lots_data.append({
            'id': lot.id,
            'prime_location_name': lot.name,
            'address': lot.city,
            'pincode': pincode,
            'price': price,
            'number_of_spots': len([s for s in lot.slots if s.is_available])
        })
    return jsonify(lots_data)

@app.route('/api/user/lots/<int:lot_id>/spots', methods=['GET'])
@jwt_required()
def api_user_lot_spots(lot_id):
    spots = ParkingSlot.query.filter_by(zone_id=lot_id, is_available=True).all()
    return jsonify([{
        'id': spot.id,
        'slot_number': spot.slot_number,
        'price_per_hour': spot.price_per_hour,
        'location': spot.location
    } for spot in spots])

@app.route('/api/user/book', methods=['POST'])
@jwt_required()
def api_book_spot():
    user_id = int(get_jwt_identity())  # Convert string to int
    data = request.get_json()
    lot_id = data.get('lot_id')
    vehicle_number = data.get('vehicle_number')
    duration = data.get('duration', 1)

    # Find available spot in the lot
    available_spot = ParkingSlot.query.filter_by(zone_id=lot_id, is_available=True).first()
    if not available_spot:
        return jsonify({'error': 'No available spots in this lot'}), 400

    # Create booking
    booking = Booking(
        user_id=user_id,
        slot_id=available_spot.id,
        vehicle_number=vehicle_number,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=duration),
        status='active'
    )
    
    available_spot.is_available = False
    db.session.add(booking)
    db.session.commit()

    return jsonify({'message': 'Spot booked successfully', 'booking_id': booking.id})

@app.route('/api/user/release', methods=['POST'])
@jwt_required()
def api_release_spot():
    user_id = int(get_jwt_identity())  # Convert string to int
    data = request.get_json()
    reservation_id = data.get('reservation_id')

    booking = Booking.query.filter_by(id=reservation_id, user_id=user_id).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    booking.status = 'completed'
    booking.end_time = datetime.utcnow()
    
    # Calculate cost based on duration and price per hour
    duration = (booking.end_time - booking.start_time).total_seconds() / 3600  # hours
    cost = duration * booking.slot.price_per_hour

    # Free up the spot
    booking.slot.is_available = True
    db.session.commit()

    return jsonify({'message': 'Spot released successfully', 'cost': cost})

@app.route('/api/user/reservations', methods=['GET'])
@jwt_required()
def api_user_reservations():
    user_id = int(get_jwt_identity())  # Convert string to int
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.start_time.desc()).all()
    
    reservations_data = []
    for booking in bookings:
        # Calculate cost for completed bookings
        parking_cost = None
        if booking.status == 'completed':
            duration = (booking.end_time - booking.start_time).total_seconds() / 3600
            parking_cost = duration * booking.slot.price_per_hour
        
        reservations_data.append({
            'id': booking.id,
            'vehicle_number': booking.vehicle_number,
            'parking_timestamp': booking.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'leaving_timestamp': booking.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': booking.status,
            'parking_cost': parking_cost,
            'payment_id': booking.payment.id if booking.payment else None,
            'slot_location': booking.slot.location,
            'slot_number': booking.slot.slot_number
        })
    
    return jsonify(reservations_data)

# Payment endpoints
@app.route('/api/user/payment', methods=['POST'])
@jwt_required()
def api_create_payment():
    user_id = int(get_jwt_identity())  # Convert string to int
    data = request.get_json()
    reservation_id = data.get('reservation_id')
    method = data.get('method', 'cash')

    booking = Booking.query.filter_by(id=reservation_id, user_id=user_id).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    
    # Only allow payment for completed bookings
    if booking.status != 'completed':
        return jsonify({'error': 'Payment can only be made for completed bookings'}), 400
    
    # Check if payment already exists
    if booking.payment:
        return jsonify({'error': 'Payment already exists for this booking'}), 400
    
    # Calculate amount based on duration and price per hour
    duration = (booking.end_time - booking.start_time).total_seconds() / 3600  # hours
    amount = duration * booking.slot.price_per_hour

    payment = Payment(
        booking_id=reservation_id,
        amount=amount,
        method=method
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({
        'message': 'Payment created successfully', 
        'payment_id': payment.id,
        'amount': amount
    })

# QR Code Payment endpoint
@app.route('/api/user/payment/qr/<int:reservation_id>', methods=['GET'])
@jwt_required()
def api_generate_payment_qr(reservation_id):
    try:
        user_id = int(get_jwt_identity())
        booking = Booking.query.filter_by(id=reservation_id, user_id=user_id).first()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.status != 'completed':
            return jsonify({'error': 'Payment can only be made for completed bookings'}), 400
        
        if booking.payment:
            return jsonify({'error': 'Payment already exists for this booking'}), 400
        
        # Calculate amount based on duration and price per hour
        duration = (booking.end_time - booking.start_time).total_seconds() / 3600  # hours
        amount = duration * booking.slot.price_per_hour
        
        # Create payment data for QR code
        payment_data = {
            'booking_id': booking.id,
            'amount': round(amount, 2),
            'user_name': booking.user.fullname,
            'vehicle_number': booking.vehicle_number,
            'location': booking.slot.location,
            'duration_hours': round(duration, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Create UPI payment string (standard format)
        upi_payment_string = f"upi://pay?pa=parking@pay&pn=Parking%20Payment&am={amount:.2f}&tn=Booking%20{booking.id}&cu=INR"
        
        try:
            # Generate QR code using qrcode.make() which handles PIL internally
            qr_img = qrcode.make(upi_payment_string)
            
            # Convert to base64
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return jsonify({
                'qr_code': f"data:image/png;base64,{qr_base64}",
                'payment_data': payment_data,
                'upi_string': upi_payment_string
            })
            
        except Exception as qr_error:
            print(f"QR code generation failed: {qr_error}")
            # Fallback: return payment data without QR code
            return jsonify({
                'qr_code': None,
                'payment_data': payment_data,
                'upi_string': upi_payment_string,
                'error': 'QR code generation failed, but payment data is available'
            })
        
    except Exception as e:
        print("Error generating QR code:", str(e))
        return jsonify({'error': f'Failed to generate QR code: {str(e)}'}), 500

# Export and bill endpoints
@app.route('/api/user/export-csv', methods=['GET'])
@jwt_required()
def api_export_csv():
    user_id = int(get_jwt_identity())  # Convert string to int
    bookings = Booking.query.filter_by(user_id=user_id).all()
    
    csv_content = "Booking ID,Vehicle,Start Time,End Time,Status,Cost\n"
    for booking in bookings:
        csv_content += f"{booking.id},{booking.vehicle_number},{booking.start_time},{booking.end_time},{booking.status},{booking.slot.price_per_hour}\n"
    
    return jsonify({'csv_content': csv_content})

@app.route('/api/user/bill/<int:payment_id>', methods=['GET'])
@jwt_required()
def api_get_bill(payment_id):
    user_id = int(get_jwt_identity())  # Convert string to int
    payment = Payment.query.filter_by(id=payment_id).first()
    
    if not payment or payment.booking.user_id != user_id:
        return jsonify({'error': 'Payment not found'}), 404

    bill_content = f"""
    PARKING BILL
    ============
    Payment ID: {payment.id}
    Date: {payment.paid_at.strftime('%Y-%m-%d %H:%M:%S')}
    Customer: {payment.booking.user.fullname}
    Vehicle: {payment.booking.vehicle_number}
    Location: {payment.booking.slot.location}
    Duration: {payment.booking.start_time.strftime('%H:%M')} - {payment.booking.end_time.strftime('%H:%M')}
    Amount: ₹{payment.amount:.2f}
    Method: {payment.method}
    """
    
    return jsonify({'bill_content': bill_content})

@app.route('/api/user/download-bill/<int:payment_id>', methods=['GET'])
@jwt_required()
def api_download_bill(payment_id):
    user_id = int(get_jwt_identity())  # Convert string to int
    payment = Payment.query.filter_by(id=payment_id).first()
    
    if not payment or payment.booking.user_id != user_id:
        return jsonify({'error': 'Payment not found'}), 404

    bill_content = f"""
    PARKING BILL
    ============
    Payment ID: {payment.id}
    Date: {payment.paid_at.strftime('%Y-%m-%d %H:%M:%S')}
    Customer: {payment.booking.user.fullname}
    Vehicle: {payment.booking.vehicle_number}
    Location: {payment.booking.slot.location}
    Duration: {payment.booking.start_time.strftime('%H:%M')} - {payment.booking.end_time.strftime('%H:%M')}
    Amount: ₹{payment.amount:.2f}
    Method: {payment.method}
    """
    
    # Create file-like object
    bill_buffer = io.BytesIO()
    bill_buffer.write(bill_content.encode('utf-8'))
    bill_buffer.seek(0)
    
    return send_file(
        bill_buffer,
        as_attachment=True,
        download_name=f'bill_{payment.id}.txt',
        mimetype='text/plain'
    )

# Test endpoint to create a sample user (for testing purposes)
@app.route('/api/test/create-user', methods=['POST'])
def api_create_test_user():
    try:
        # Create a test user
        test_user = User(
            email='test@user.com',
            password='password123',
            fullname='Test User',
            address='Test Address',
            pincode='123456'
        )
        db.session.add(test_user)
        db.session.commit()
        print("Test user created successfully!")
        return jsonify({'message': 'Test user created successfully'})
    except Exception as e:
        db.session.rollback()
        print("Error creating test user:", str(e))
        return jsonify({'error': f'Failed to create test user: {str(e)}'}), 500

# Admin user management endpoints
@app.route('/api/users', methods=['GET'])
@jwt_required()
def api_get_users():
    try:
        # Check if user is admin
        user_id = int(get_jwt_identity())  # Convert string to int
        admin = Admin.query.get(user_id)
        if not admin:
            print("Non-admin user tried to access users endpoint")  # Debug print
            return jsonify({'error': 'Admin access required'}), 403
        
        print("Getting users for admin:", admin.email)  # Debug print
        users = User.query.all()
        print(f"Found {len(users)} users")  # Debug print
        
        user_list = [{
            'id': user.id,
            'email': user.email,
            'fullname': user.fullname,
            'address': user.address,
            'pincode': user.pincode
        } for user in users]
        
        print("Returning users:", user_list)  # Debug print
        return jsonify(user_list)
    except Exception as e:
        print("Error getting users:", str(e))  # Debug print
        return jsonify({'error': f'Failed to get users: {str(e)}'}), 500

@app.route('/api/admin/users', methods=['POST'])
@jwt_required()
def api_admin_create_user():
    try:
        # Check if user is admin
        admin_id = int(get_jwt_identity())  # Convert string to int
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        fullname = data.get('fullname')
        address = data.get('address')
        pincode = data.get('pincode')

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409

        new_user = User(email=email, password=password, fullname=fullname,
                        address=address, pincode=pincode)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'fullname': new_user.fullname,
                'address': new_user.address,
                'pincode': new_user.pincode
            }
        })
    except Exception as e:
        db.session.rollback()
        print("Error creating user:", str(e))  # Debug print
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def api_delete_user(user_id):
    try:
        # Check if user is admin
        admin_id = int(get_jwt_identity())  # Convert string to int
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Delete user's bookings and payments
        for booking in user.bookings:
            if booking.payment:
                db.session.delete(booking.payment)
            db.session.delete(booking)
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print("Error deleting user:", str(e))  # Debug print
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def api_update_user(user_id):
    try:
        # Check if user is admin
        admin_id = int(get_jwt_identity())  # Convert string to int
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        user.fullname = data.get('fullname', user.fullname)
        user.address = data.get('address', user.address)
        user.pincode = data.get('pincode', user.pincode)
        
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        print("Error updating user:", str(e))  # Debug print
        return jsonify({'error': f'Failed to update user: {str(e)}'}), 500

@app.route('/api/admin/summary', methods=['GET'])
@jwt_required()
def api_admin_summary():
    try:
        # Check if user is admin
        admin_id = int(get_jwt_identity())  # Convert string to int
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        # Calculate summary statistics
        total_users = User.query.count()
        total_bookings = Booking.query.count()
        total_payments = Payment.query.count()
        total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0
        
        return jsonify({
            'total_users': total_users,
            'total_bookings': total_bookings,
            'total_payments': total_payments,
            'total_revenue': round(total_revenue, 2)
        })
    except Exception as e:
        print("Error getting admin summary:", str(e))  # Debug print
        return jsonify({'error': f'Failed to get admin summary: {str(e)}'}), 500

@app.route('/api/user/summary', methods=['GET'])
@jwt_required()
def api_user_summary():
    user_id = int(get_jwt_identity())  # Convert string to int
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Calculate summary statistics
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    
    user_total_spent = db.session.query(func.sum(Payment.amount)).join(Booking).filter(Booking.user_id == user_id).scalar() or 0
    user_total_time = db.session.query(func.sum(func.extract('epoch', Booking.end_time - Booking.start_time) / 3600)).filter(Booking.user_id == user_id).scalar() or 0
    user_payment_count = db.session.query(func.count(Payment.id)).join(Booking).filter(Booking.user_id == user_id).scalar() or 0
    user_booking_count = Booking.query.filter_by(user_id=user_id).count()

    return jsonify({
        'total_users': total_users,
        'total_bookings': total_bookings,
        'user_total_spent': round(user_total_spent, 2),
        'user_total_time': round(user_total_time, 2),
        'user_payment_count': user_payment_count,
        'user_booking_count': user_booking_count
    })

# Original Flask routes (for reference, but not used by Vue)
@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        address = request.form['address']
        pincode = request.form['pincode']

        new_user = User(email=email, password=password, fullname=fullname,
                        address=address, pincode=pincode)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/')

    return render_template('signuser.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['userfn'] = user.fullname
            return redirect(url_for('user_profile', id=user.id))
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/user<int:id>')
def user_profile(id):
    user = User.query.get(id)
    if not user:
        return "User not found", 404

    history = Booking.query.filter_by(user_id=id).order_by(Booking.start_time.desc()).limit(5).all()
    return render_template('user_dashboard.html', user=user, id=id, history=history)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/user/<int:id>/edit', methods=['GET', 'POST'])
def edit_profile_user(id):
    user = User.query.get(id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        user.fullname = request.form['fullname']
        user.address = request.form['address']
        user.pincode = request.form['pincode']
        db.session.commit()
        return redirect(url_for('user_profile', id=id))

    return render_template('editprofileuser.html', user=user, id=id)

@app.route('/summary/<int:id>')
def summary(id):
    total_users = User.query.count()
    total_bookings = Booking.query.count()

    user = User.query.get(id)
    if not user:
        return "User not found", 404

    user_total_spent = db.session.query(func.sum(Payment.amount)).join(Booking).filter(Booking.user_id == id).scalar() or 0
    
    user_total_time = db.session.query(func.sum(func.extract('epoch', Booking.end_time - Booking.start_time) / 3600)).filter(Booking.user_id == id).scalar() or 0
    
    user_payment_count = db.session.query(func.count(Payment.id)).join(Booking).filter(Booking.user_id == id).scalar() or 0
    
    user_booking_count = Booking.query.filter_by(user_id=id).count()

    return render_template('summary.html',
                           total_users=total_users,
                           total_bookings=total_bookings,
                           id=user.id,
                           userfn=user.fullname,
                           user_total_spent=round(user_total_spent, 2),
                           user_total_time=round(user_total_time, 2),
                           user_payment_count=user_payment_count,
                           user_booking_count=user_booking_count)

# Keep all your original API endpoints and admin routes here...
# (I'm keeping the structure but focusing on the Vue-compatible endpoints above)

if __name__ == '__main__':
    app.run(debug=True) 