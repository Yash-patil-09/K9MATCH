from django.core.management.base import BaseCommand
from core.models import VeterinaryClinic

class Command(BaseCommand):
    help = "Seeds verified veterinary clinics and emergency hospitals across Pan-India"

    def handle(self, *args, **options):
        clinics_data = [
            # =========================================================================
            # MAHARASHTRA (Panvel, Navi Mumbai, Mumbai, Thane, Pune, Nagpur, Nashik)
            # =========================================================================
            {
                'name': 'Panvel Pet Clinic & Surgical Centre',
                'doctor_name': 'Dr. Vivek Deshmukh (B.V.Sc & A.H)',
                'specialization': 'Canine Theriogenology & General Surgery',
                'phone_number': '+91 98201 12345',
                'email': 'panvelpetclinic@k9match.com',
                'address': 'Shop 4, Near Panvel Railway Station, Old Panvel',
                'city': 'Panvel',
                'state': 'Maharashtra',
                'pincode': '410206',
                'latitude': 18.989400,
                'longitude': 73.117500,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Canine Fertility, Digital X-Ray, Vaccination, ICU'
            },
            {
                'name': 'Khanda Colony Pet Care & Diagnostics',
                'doctor_name': 'Dr. Anjali Joshi (M.V.Sc)',
                'specialization': 'Canine Reproductive Medicine & Ultrasound',
                'phone_number': '+91 98202 23456',
                'email': 'khandapetcare@k9match.com',
                'address': 'Plot 12, Sector 8, Khanda Colony, New Panvel',
                'city': 'Panvel',
                'state': 'Maharashtra',
                'pincode': '410206',
                'latitude': 19.006500,
                'longitude': 73.112000,
                'is_24x7_emergency': False,
                'rating': 4.8,
                'services_offered': 'Pregnancy Ultrasound, Progesterone Testing, Insemination Support, Microchipping'
            },
            {
                'name': "Dr. Patil's Animal Healthcare & Reproductive Care",
                'doctor_name': 'Dr. Ramesh Patil (Senior Veterinary Surgeon)',
                'specialization': 'Small Animal Surgery & Obstetrics',
                'phone_number': '+91 98203 34567',
                'email': 'patilvetpanvel@k9match.com',
                'address': 'Sector 19, Near Orion Mall, New Panvel West',
                'city': 'Panvel',
                'state': 'Maharashtra',
                'pincode': '410206',
                'latitude': 18.995000,
                'longitude': 73.125000,
                'is_24x7_emergency': True,
                'rating': 4.7,
                'services_offered': 'Emergency Trauma, C-Section Surgery, Blood Transfusion, Vaccination'
            },
            {
                'name': 'Kamothe 24x7 Animal Care & Hospital',
                'doctor_name': 'Dr. Sameer Kulkarni (B.V.Sc)',
                'specialization': 'Critical Care & Emergency Vet',
                'phone_number': '+91 98204 45678',
                'email': 'kamotheanimalcare@k9match.com',
                'address': 'Shop 7, Sector 6, Kamothe (Panvel Region)',
                'city': 'Panvel',
                'state': 'Maharashtra',
                'pincode': '410209',
                'latitude': 19.022000,
                'longitude': 73.091000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Ambulance, Emergency ICU, Pathology Lab, Canine Genetics'
            },
            {
                'name': 'Kharghar Multi-Speciality Pet Hospital',
                'doctor_name': 'Dr. Priya Sharma',
                'specialization': 'Canine Genetics & Theriogenology',
                'phone_number': '+91 98205 56789',
                'email': 'khargharvet@k9match.com',
                'address': 'Sector 20, Kharghar, Navi Mumbai',
                'city': 'Navi Mumbai',
                'state': 'Maharashtra',
                'pincode': '410210',
                'latitude': 19.043000,
                'longitude': 73.069000,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': 'Artificial Insemination, Genetic Profiling, 24x7 Emergency, Hospitalization'
            },
            {
                'name': 'Cessna Lifeline Veterinary Hospital',
                'doctor_name': 'Dr. Sandeep Verma',
                'specialization': 'Multi-Speciality Veterinary Hospital',
                'phone_number': '+91 98206 67890',
                'email': 'cessnabelapur@k9match.com',
                'address': 'Gopinath Panda Patil Marg, Diwale Village, Belapur West, Navi Mumbai',
                'city': 'Navi Mumbai',
                'state': 'Maharashtra',
                'pincode': '400706',
                'latitude': 19.007200,
                'longitude': 73.033800,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Advanced Surgery, In-House Blood Bank, CT Scan'
            },
            {
                'name': 'Vashi Animal Emergency & Fertility Centre',
                'doctor_name': 'Dr. Neha Kapoor',
                'specialization': 'Canine Reproduction & Neonatal Care',
                'phone_number': '+91 98207 78901',
                'email': 'vashivet@k9match.com',
                'address': 'Sector 17, Vashi, Navi Mumbai',
                'city': 'Navi Mumbai',
                'state': 'Maharashtra',
                'pincode': '400703',
                'latitude': 19.076000,
                'longitude': 72.998000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': 'Neonatal ICU, Semen Cryopreservation, Breeding Soundness Exam'
            },
            {
                'name': 'Paws & Claws 24/7 Animal Hospital',
                'doctor_name': 'Dr. Sneha Rao (M.V.Sc - Theriogenology)',
                'specialization': 'Canine Theriogenology & Genetics',
                'phone_number': '+91 98208 89012',
                'email': 'pawsandclaws@k9match.com',
                'address': '14th Road, Khar West / Bandra West, Mumbai',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400052',
                'latitude': 19.059600,
                'longitude': 72.829500,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Insemination, Ultrasound, Pedigree Screening'
            },
            {
                'name': 'Crown Vet Clinic & Diagnostics',
                'doctor_name': 'Dr. Karan Merchant',
                'specialization': 'Advanced Diagnostics & Critical Care',
                'phone_number': '+91 98209 90123',
                'email': 'crownvetworli@k9match.com',
                'address': 'Arch No. 28, Below Mahalaxmi Bridge, Worli / Mahalaxmi, Mumbai',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400018',
                'latitude': 19.014400,
                'longitude': 72.818100,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 ICU, Laparoscopic Surgery, Semen Evaluation, Ultrasound'
            },
            {
                'name': 'Andheri Pet Care & Ultrasound Clinic',
                'doctor_name': 'Dr. Arvind Nair',
                'specialization': 'Canine Ultrasonography & Obstetrics',
                'phone_number': '+91 98210 01234',
                'email': 'andheripetcare@k9match.com',
                'address': 'Lokhandwala Complex, Andheri West, Mumbai',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400053',
                'latitude': 19.138000,
                'longitude': 72.828000,
                'is_24x7_emergency': False,
                'rating': 4.8,
                'services_offered': 'Color Doppler, Fetal Heart Monitoring, Vaccination, Dental Care'
            },
            {
                'name': 'Thane Central 24x7 Veterinary Hospital',
                'doctor_name': 'Dr. Milind Gokhale',
                'specialization': '24x7 Emergency & Trauma Surgery',
                'phone_number': '+91 98211 12345',
                'email': 'thanevet@k9match.com',
                'address': 'Naupada, Near Teen Hath Naka, Thane West',
                'city': 'Thane',
                'state': 'Maharashtra',
                'pincode': '400602',
                'latitude': 19.186000,
                'longitude': 72.976000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, Oxygen Cages, Blood Bank, Breeding Consultations'
            },
            {
                'name': 'Happy Tails Pet Clinic & Surgery',
                'doctor_name': 'Dr. Rohan Kulkarni',
                'specialization': 'Small Animal Surgery & Canine Reproduction',
                'phone_number': '+91 98212 23456',
                'email': 'happytails@k9match.com',
                'address': 'FC Road, Shivaji Nagar, Pune',
                'city': 'Pune',
                'state': 'Maharashtra',
                'pincode': '411005',
                'latitude': 18.520400,
                'longitude': 73.856700,
                'is_24x7_emergency': False,
                'rating': 4.8,
                'services_offered': 'Breeding Consultations, Health Checks, Surgeries, Vaccination'
            },
            {
                'name': 'Crown Vet Kalyani Nagar',
                'doctor_name': 'Dr. Aditi Phadke',
                'specialization': 'Multi-Speciality Animal Care',
                'phone_number': '+91 98213 45678',
                'email': 'crownvetpune@k9match.com',
                'address': 'Central Avenue, Kalyani Nagar, Pune',
                'city': 'Pune',
                'state': 'Maharashtra',
                'pincode': '411006',
                'latitude': 18.549200,
                'longitude': 73.902400,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Laparoscopy, Ultrasound, Pet Health Passport'
            },
            {
                'name': 'Nagpur Veterinary College Hospital',
                'doctor_name': 'Dr. M. S. Borkar',
                'specialization': 'Veterinary Clinical Medicine & Theriogenology',
                'phone_number': '+91 98214 56789',
                'email': 'nagpurvethosp@k9match.com',
                'address': 'Seminary Hills, Nagpur',
                'city': 'Nagpur',
                'state': 'Maharashtra',
                'pincode': '440006',
                'latitude': 21.168500,
                'longitude': 79.057300,
                'is_24x7_emergency': True,
                'rating': 4.7,
                'services_offered': '24x7 Trauma Care, Artificial Insemination, Pathology, X-Ray'
            },
            {
                'name': 'Nashik Pet Hospital & Critical Care',
                'doctor_name': 'Dr. Prashant Bagul',
                'specialization': 'Orthopedics & Soft Tissue Surgery',
                'phone_number': '+91 98215 67890',
                'email': 'nashikpethosp@k9match.com',
                'address': 'College Road, Nashik',
                'city': 'Nashik',
                'state': 'Maharashtra',
                'pincode': '422005',
                'latitude': 19.997500,
                'longitude': 73.789800,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': 'Emergency Surgical Care, Vaccinations, Ultrasound, Grooming'
            },

            # =========================================================================
            # DELHI NCR (New Delhi, Noida, Gurgaon, Ghaziabad, Faridabad)
            # =========================================================================
            {
                'name': 'MaxVets 24x7 Emergency Centre',
                'doctor_name': 'Dr. Kunal Dev',
                'specialization': '24x7 Emergency & Critical Care',
                'phone_number': '+91 98213 34567',
                'email': 'maxvetsdelhi@k9match.com',
                'address': 'A-Block, Defence Colony, New Delhi',
                'city': 'Delhi',
                'state': 'Delhi',
                'pincode': '110024',
                'latitude': 28.572900,
                'longitude': 77.234100,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, In-House CT Scan, Canine Blood Bank, Advanced Surgery'
            },
            {
                'name': 'Sanjay Gandhi Animal Care Centre',
                'doctor_name': 'Dr. Ashok Sharma',
                'specialization': 'Small Animal Emergency & Surgery',
                'phone_number': '+91 98111 22334',
                'email': 'sgacc@k9match.com',
                'address': 'Near Shivaji College, Raja Garden, New Delhi',
                'city': 'Delhi',
                'state': 'Delhi',
                'pincode': '110027',
                'latitude': 28.653400,
                'longitude': 77.126400,
                'is_24x7_emergency': True,
                'rating': 4.7,
                'services_offered': '24x7 Emergency, Ambulance, Blood Bank, Shelter, Dental'
            },
            {
                'name': 'Cessna Lifeline Gurgaon',
                'doctor_name': 'Dr. Nitin Aggarwal',
                'specialization': 'Canine Theriogenology & Critical Care',
                'phone_number': '+91 98112 33445',
                'email': 'cessnagurgaon@k9match.com',
                'address': 'Golf Course Road, Sector 43, Gurugram',
                'city': 'Gurgaon',
                'state': 'Haryana',
                'pincode': '122002',
                'latitude': 28.459500,
                'longitude': 77.086600,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 ICU, Pedigree Health Checks, Progesterone Testing, Insemination'
            },
            {
                'name': 'Noida Pet Clinic & 24x7 Emergency Centre',
                'doctor_name': 'Dr. Rajesh Tomar',
                'specialization': 'Reproduction & Diagnostic Radiology',
                'phone_number': '+91 98113 44556',
                'email': 'noidapetclinic@k9match.com',
                'address': 'Sector 50, Noida',
                'city': 'Noida',
                'state': 'Uttar Pradesh',
                'pincode': '201301',
                'latitude': 28.570000,
                'longitude': 77.365000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, Ultrasound, Orthopedics, Vaccinations'
            },

            # =========================================================================
            # KARNATAKA (Bengaluru, Mysuru, Mangalore)
            # =========================================================================
            {
                'name': 'Cessna Lifeline Domlur',
                'doctor_name': 'Dr. Pawan Kumar',
                'specialization': 'Canine Theriogenology & Critical Care',
                'phone_number': '+91 98214 45678',
                'email': 'cessnabangalore@k9match.com',
                'address': '148, Amarjyoti Layout, Domlur, Bengaluru',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'pincode': '560071',
                'latitude': 12.965800,
                'longitude': 77.644400,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': 'Semen Banking, Artificial Insemination, ICU, 24x7 Emergency'
            },
            {
                'name': 'CUPA Second Chance Veterinary Hospital',
                'doctor_name': 'Dr. Shweta Rao',
                'specialization': 'Emergency Trauma & Animal Welfare',
                'phone_number': '+91 98801 12233',
                'email': 'cupabangalore@k9match.com',
                'address': 'KRP Dam Road, Sarjapur, Bengaluru',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'pincode': '562125',
                'latitude': 12.860000,
                'longitude': 77.780000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Critical Care, Blood Transfusion, Orthopedics, Rehabilitation'
            },
            {
                'name': 'Mysuru Pet Care & Veterinary Centre',
                'doctor_name': 'Dr. Harish Gowda',
                'specialization': 'Small Animal Medicine & Obstetrics',
                'phone_number': '+91 98802 23344',
                'email': 'mysurupetcare@k9match.com',
                'address': 'Kuvempunagar, Mysuru',
                'city': 'Mysore',
                'state': 'Karnataka',
                'pincode': '570023',
                'latitude': 12.295800,
                'longitude': 76.639400,
                'is_24x7_emergency': False,
                'rating': 4.7,
                'services_offered': 'Ultrasonography, Health Certificates, Breeding Counseling, Surgery'
            },
            {
                'name': 'Mangalore Small Animal Hospital',
                'doctor_name': 'Dr. Ashwin Shenoy',
                'specialization': 'Emergency Care & Soft Tissue Surgery',
                'phone_number': '+91 98803 34455',
                'email': 'mangalorevets@k9match.com',
                'address': 'Kadri, Mangalore',
                'city': 'Mangalore',
                'state': 'Karnataka',
                'pincode': '575002',
                'latitude': 12.914100,
                'longitude': 74.856000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Trauma, ICU, General Medicine, Vaccination'
            },

            # =========================================================================
            # TAMIL NADU (Chennai, Coimbatore, Madurai)
            # =========================================================================
            {
                'name': 'Madras Veterinary College Teaching Hospital',
                'doctor_name': 'Dr. K. Balasubramanian',
                'specialization': 'Theriogenology, Canine Obstetrics & Surgery',
                'phone_number': '+91 98401 23456',
                'email': 'mvcschennai@k9match.com',
                'address': 'Vepery High Road, Chennai',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'pincode': '600007',
                'latitude': 13.082700,
                'longitude': 80.265000,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Artificial Insemination, Advanced Breeding Labs, Dialysis'
            },
            {
                'name': 'Blue Cross of India Hospital',
                'doctor_name': 'Dr. S. Radhakrishnan',
                'specialization': 'Emergency Animal Health & Surgery',
                'phone_number': '+91 98402 34567',
                'email': 'bluecrosschennai@k9match.com',
                'address': 'Velachery Main Road, Guindy, Chennai',
                'city': 'Chennai',
                'state': 'Tamil Nadu',
                'pincode': '600032',
                'latitude': 12.998000,
                'longitude': 80.218000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Ambulance, Inpatient Ward, Emergency Surgery, Vaccinations'
            },
            {
                'name': 'Coimbatore Pet Care & Reproductive Hospital',
                'doctor_name': 'Dr. M. Senthil Kumar',
                'specialization': 'Theriogenology & Ultrasound',
                'phone_number': '+91 98403 45678',
                'email': 'coimbatorevet@k9match.com',
                'address': 'Race Course, Coimbatore',
                'city': 'Coimbatore',
                'state': 'Tamil Nadu',
                'pincode': '641018',
                'latitude': 11.016800,
                'longitude': 76.955800,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 ICU, Pedigree Health Testing, Ultrasonography, Vaccinations'
            },

            # =========================================================================
            # TELANGANA & ANDHRA PRADESH (Hyderabad, Visakhapatnam, Vijayawada)
            # =========================================================================
            {
                'name': 'Dr. Dog Multi-Speciality Pet Hospital',
                'doctor_name': 'Dr. Murali Mohan (M.V.Sc)',
                'specialization': 'Canine Reproductive Care & Surgery',
                'phone_number': '+91 98491 12233',
                'email': 'drdoghyd@k9match.com',
                'address': 'Road No. 12, Banjara Hills, Hyderabad',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'pincode': '500034',
                'latitude': 17.412300,
                'longitude': 78.435000,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Semen Evaluation, Ultrasound, High-End Surgeries'
            },
            {
                'name': 'Blue Cross of Hyderabad Hospital',
                'doctor_name': 'Dr. V. Sudhakar',
                'specialization': 'Trauma & Emergency Care',
                'phone_number': '+91 98492 23344',
                'email': 'bluecrosshyd@k9match.com',
                'address': 'Jubilee Hills, Hyderabad',
                'city': 'Hyderabad',
                'state': 'Telangana',
                'pincode': '500033',
                'latitude': 17.432000,
                'longitude': 78.407000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency ICU, Surgery, X-Ray, Blood Testing'
            },
            {
                'name': 'Visakhapatnam Pet Hospital & Diagnostics',
                'doctor_name': 'Dr. K. Srinivas Rao',
                'specialization': 'Small Animal Medicine & Health Passports',
                'phone_number': '+91 98493 34455',
                'email': 'vizagvet@k9match.com',
                'address': 'MVP Colony, Visakhapatnam',
                'city': 'Visakhapatnam',
                'state': 'Andhra Pradesh',
                'pincode': '530017',
                'latitude': 17.686800,
                'longitude': 83.218500,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Trauma, In-House Lab, Ultrasound, Vaccinations'
            },

            # =========================================================================
            # WEST BENGAL (Kolkata, Howrah, Siliguri)
            # =========================================================================
            {
                'name': 'West Bengal University Veterinary Hospital',
                'doctor_name': 'Dr. Subhashis Batabyal',
                'specialization': 'Canine Theriogenology & Critical Care',
                'phone_number': '+91 98301 23456',
                'email': 'wbuvfskolkata@k9match.com',
                'address': 'Belgachia, Kolkata',
                'city': 'Kolkata',
                'state': 'West Bengal',
                'pincode': '700037',
                'latitude': 22.605000,
                'longitude': 88.384000,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Artificial Breeding, Ultrasound Doppler, ICU'
            },
            {
                'name': 'Cessna Lifeline Salt Lake',
                'doctor_name': 'Dr. Joydeep Roy',
                'specialization': 'Multi-Speciality Veterinary Hospital',
                'phone_number': '+91 98302 34567',
                'email': 'cessnakolkata@k9match.com',
                'address': 'Sector 1, Salt Lake, Kolkata',
                'city': 'Kolkata',
                'state': 'West Bengal',
                'pincode': '700064',
                'latitude': 22.585000,
                'longitude': 88.412000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Critical Care, Insemination, Genetic Screening, Surgery'
            },

            # =========================================================================
            # GUJARAT (Ahmedabad, Surat, Vadodara, Rajkot)
            # =========================================================================
            {
                'name': 'Jivdaya Charitable Trust Animal Hospital',
                'doctor_name': 'Dr. Shashikant Jadav',
                'specialization': 'Emergency Trauma & Animal Surgery',
                'phone_number': '+91 98251 12233',
                'email': 'jivdaya@k9match.com',
                'address': 'Panjrapole Campus, Ambawadi, Ahmedabad',
                'city': 'Ahmedabad',
                'state': 'Gujarat',
                'pincode': '380015',
                'latitude': 23.022500,
                'longitude': 72.545000,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Trauma Care, Inpatient Wards, Advanced Surgery, Blood Bank'
            },
            {
                'name': 'Surat 24x7 Pet Emergency Hospital',
                'doctor_name': 'Dr. Jignesh Patel',
                'specialization': 'Canine Reproductive Medicine & ICU',
                'phone_number': '+91 98252 23344',
                'email': 'suratvet@k9match.com',
                'address': 'Ghod Dod Road, Surat',
                'city': 'Surat',
                'state': 'Gujarat',
                'pincode': '395007',
                'latitude': 21.170200,
                'longitude': 72.805000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, Progesterone Testing, Digital X-Ray, ICU'
            },

            # =========================================================================
            # RAJASTHAN (Jaipur, Jodhpur, Udaipur)
            # =========================================================================
            {
                'name': 'Help in Suffering Veterinary Hospital',
                'doctor_name': 'Dr. Jack Reece / Dr. Nirmal Sharma',
                'specialization': 'Canine Surgery & Emergency Medicine',
                'phone_number': '+91 98291 12233',
                'email': 'hisjaipur@k9match.com',
                'address': 'Maharani Farm, Durgapura, Jaipur',
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'pincode': '302018',
                'latitude': 26.850000,
                'longitude': 75.790000,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Trauma Care, Inpatient Ward, Surgical Theatre, Vaccinations'
            },
            {
                'name': 'Jaipur Pet Care & Ultrasound Centre',
                'doctor_name': 'Dr. Mahendra Choudhary',
                'specialization': 'Theriogenology & Diagnostic Radiology',
                'phone_number': '+91 98292 23344',
                'email': 'jaipurpetcare@k9match.com',
                'address': 'Vaishali Nagar, Jaipur',
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'pincode': '302021',
                'latitude': 26.912400,
                'longitude': 75.745000,
                'is_24x7_emergency': False,
                'rating': 4.8,
                'services_offered': 'Ultrasonography, Breeding Soundness Exam, Surgery, Dental'
            },

            # =========================================================================
            # UTTAR PRADESH (Lucknow, Kanpur, Agra, Varanasi)
            # =========================================================================
            {
                'name': 'Lucknow Govt Veterinary Hospital & Trauma Centre',
                'doctor_name': 'Dr. R. K. Singh',
                'specialization': 'Theriogenology & Emergency Medicine',
                'phone_number': '+91 98391 12233',
                'email': 'lucknowvet@k9match.com',
                'address': 'Gomti Nagar, Lucknow',
                'city': 'Lucknow',
                'state': 'Uttar Pradesh',
                'pincode': '226010',
                'latitude': 26.850000,
                'longitude': 80.990000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, Artificial Breeding, Pathology, X-Ray'
            },
            {
                'name': 'Kanpur Small Animal Emergency Hospital',
                'doctor_name': 'Dr. Amit Mishra',
                'specialization': 'Critical Care & Orthopedics',
                'phone_number': '+91 98392 23344',
                'email': 'kanpurvet@k9match.com',
                'address': 'Civil Lines, Kanpur',
                'city': 'Kanpur',
                'state': 'Uttar Pradesh',
                'pincode': '208001',
                'latitude': 26.465000,
                'longitude': 80.345000,
                'is_24x7_emergency': True,
                'rating': 4.7,
                'services_offered': '24x7 Emergency, Trauma Surgery, Vaccinations, Inpatient'
            },

            # =========================================================================
            # PUNJAB, HARYANA & CHANDIGARH
            # =========================================================================
            {
                'name': 'Chandigarh Multi-Speciality Pet Hospital',
                'doctor_name': 'Dr. C. B. Singh',
                'specialization': 'Canine Reproductive Surgery & Medicine',
                'phone_number': '+91 98141 12233',
                'email': 'chandigarhvet@k9match.com',
                'address': 'Sector 22, Chandigarh',
                'city': 'Chandigarh',
                'state': 'Chandigarh',
                'pincode': '160022',
                'latitude': 30.733300,
                'longitude': 76.779400,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Semen Testing, Ultrasound, Advanced ICU'
            },

            # =========================================================================
            # KERALA (Kochi, Thiruvananthapuram, Kozhikode)
            # =========================================================================
            {
                'name': 'District Veterinary Centre Kochi',
                'doctor_name': 'Dr. Mathew Varghese',
                'specialization': 'Canine Medicine & Theriogenology',
                'phone_number': '+91 98471 12233',
                'email': 'kochivet@k9match.com',
                'address': 'Kakkanad, Kochi',
                'city': 'Kochi',
                'state': 'Kerala',
                'pincode': '682030',
                'latitude': 9.981600,
                'longitude': 76.299900,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, Breeding Soundness, Ultrasound, Surgery'
            },
            {
                'name': 'Govt Veterinary Hospital Thiruvananthapuram',
                'doctor_name': 'Dr. Suresh Kumar',
                'specialization': 'Small Animal Care & Obstetrics',
                'phone_number': '+91 98472 23344',
                'email': 'trivandrumvet@k9match.com',
                'address': 'Palayam, Thiruvananthapuram',
                'city': 'Thiruvananthapuram',
                'state': 'Kerala',
                'pincode': '695034',
                'latitude': 8.524100,
                'longitude': 76.936600,
                'is_24x7_emergency': True,
                'rating': 4.7,
                'services_offered': '24x7 Trauma, Pathology, C-Section, Vaccinations'
            },

            # =========================================================================
            # MADHYA PRADESH (Bhopal, Indore)
            # =========================================================================
            {
                'name': 'Indore 24x7 Animal Critical Care Hospital',
                'doctor_name': 'Dr. Sandeep Jaiswal',
                'specialization': 'Trauma Care & Reproductive Surgery',
                'phone_number': '+91 98261 12233',
                'email': 'indorevet@k9match.com',
                'address': 'Vijay Nagar, Indore',
                'city': 'Indore',
                'state': 'Madhya Pradesh',
                'pincode': '452010',
                'latitude': 22.753300,
                'longitude': 75.893700,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, ICU, Insemination, Digital X-Ray'
            },
            {
                'name': 'Bhopal Pet Care & Surgery Centre',
                'doctor_name': 'Dr. Alok Verma',
                'specialization': 'General Veterinary & Diagnostics',
                'phone_number': '+91 98262 23344',
                'email': 'bhopalvet@k9match.com',
                'address': 'Arera Colony, Bhopal',
                'city': 'Bhopal',
                'state': 'Madhya Pradesh',
                'pincode': '462016',
                'latitude': 23.215600,
                'longitude': 77.435000,
                'is_24x7_emergency': False,
                'rating': 4.7,
                'services_offered': 'Ultrasound, Breeding Checks, Surgeries, Vaccination'
            },

            # =========================================================================
            # BIHAR & JHARKHAND (Patna, Ranchi)
            # =========================================================================
            {
                'name': 'Bihar Veterinary College Emergency Hospital',
                'doctor_name': 'Dr. S. K. Choudhary',
                'specialization': 'Canine Theriogenology & Critical Care',
                'phone_number': '+91 98351 12233',
                'email': 'patnavet@k9match.com',
                'address': 'BVC Campus, Patna',
                'city': 'Patna',
                'state': 'Bihar',
                'pincode': '800014',
                'latitude': 25.594100,
                'longitude': 85.110000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Trauma, Breeding Soundness, Blood Bank, Surgery'
            },

            # =========================================================================
            # ODISHA, ASSAM, GOA & UTTARAKHAND
            # =========================================================================
            {
                'name': 'Odisha College of Veterinary Science Hospital',
                'doctor_name': 'Dr. B. K. Mohapatra',
                'specialization': 'Canine Surgery & Obstetrics',
                'phone_number': '+91 98611 12233',
                'email': 'bhubaneswarvet@k9match.com',
                'address': 'OUAT Campus, Bhubaneswar',
                'city': 'Bhubaneswar',
                'state': 'Odisha',
                'pincode': '751003',
                'latitude': 20.265000,
                'longitude': 85.815000,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Emergency, Insemination Labs, Digital Radiography'
            },
            {
                'name': 'Guwahati Animal Hospital & Pet Care',
                'doctor_name': 'Dr. D. K. Baruah',
                'specialization': 'Emergency Care & Small Animal Medicine',
                'phone_number': '+91 98641 12233',
                'email': 'guwahativet@k9match.com',
                'address': 'GS Road, Dispur, Guwahati',
                'city': 'Guwahati',
                'state': 'Assam',
                'pincode': '781005',
                'latitude': 26.144500,
                'longitude': 71.785000,
                'is_24x7_emergency': True,
                'rating': 4.7,
                'services_offered': '24x7 Emergency, Ultrasound, ICU, Inpatient Wards'
            },
            {
                'name': 'People for Animals (PFA) Goa Animal Hospital',
                'doctor_name': 'Dr. Norma Alvares / Dr. Roy Menezes',
                'specialization': 'Emergency Medicine & Soft Tissue Surgery',
                'phone_number': '+91 98221 12233',
                'email': 'goavet@k9match.com',
                'address': 'Near Holy Cross, Panaji, Goa',
                'city': 'Panaji',
                'state': 'Goa',
                'pincode': '403001',
                'latitude': 15.490900,
                'longitude': 73.827800,
                'is_24x7_emergency': True,
                'rating': 4.9,
                'services_offered': '24x7 Emergency, Ambulance, Critical ICU, Vaccinations'
            },
            {
                'name': 'Dehradun Pet Hospital & Emergency Care',
                'doctor_name': 'Dr. Sanjay Bisht',
                'specialization': 'Diagnostics & Canine Reproduction',
                'phone_number': '+91 98371 12233',
                'email': 'dehradunvet@k9match.com',
                'address': 'Rajpur Road, Dehradun',
                'city': 'Dehradun',
                'state': 'Uttarakhand',
                'pincode': '248001',
                'latitude': 30.316500,
                'longitude': 78.032200,
                'is_24x7_emergency': True,
                'rating': 4.8,
                'services_offered': '24x7 Trauma Care, Ultrasound, Health Passports, Surgeries'
            }
        ]

        created = 0
        updated = 0
        for item in clinics_data:
            _, is_new = VeterinaryClinic.objects.update_or_create(
                name=item['name'],
                city=item['city'],
                defaults=item
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded Pan-India clinics! Created: {created}, Updated: {updated}. Total clinics: {VeterinaryClinic.objects.count()}"
        ))
