import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_canine_passport_pdf(dog):
    """
    Generates an authenticated Canine Pedigree & Health Passport PDF
    using ReportLab. Returns the raw bytes of the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#004ac6")
    secondary_color = colors.HexColor("#006242")
    dark_color = colors.HexColor("#0f172a")
    gray_color = colors.HexColor("#64748b")
    light_bg = colors.HexColor("#f8fafc")
    gold_color = colors.HexColor("#b45309")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=gray_color,
        alignment=1
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceAfter=6
    )

    cell_label = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=dark_color
    )

    cell_val = ParagraphStyle(
        'CellVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=dark_color
    )

    story = []

    # Title & Header
    story.append(Paragraph("K9MATCH OFFICIAL CANINE PASSPORT", title_style))
    story.append(Paragraph("Certified Digital Pedigree & Veterinary Health Document · Welfare Compliance ID: K9M-%05d" % dog.id, subtitle_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=14))

    # Section 1: Canine Profile & Identification
    story.append(Paragraph("1. CANINE IDENTIFICATION & REGISTRY", section_heading))
    
    breed_desc = dog.breed
    if dog.secondary_breed:
        breed_desc += f" (Cross with {dog.secondary_breed})"
    
    kci_text = f"Yes · Reg #{dog.kci_number}" if (dog.kci_registered and dog.kci_number) else ("Yes (Pending Document Verification)" if dog.kci_registered else "Companion Canine (Non-KCI)")
    gender_text = f"{dog.get_gender_display()} (Sire / Stud)" if dog.gender.lower() == 'male' else f"{dog.get_gender_display()} (Dam / Female)"
    age_text = f"{dog.age_years} Years, {dog.age_months} Months"
    weight_text = f"{dog.weight} {dog.weight_unit}" if dog.weight else "Not Recorded"
    location_text = f"{dog.city}, {dog.state}" if dog.state else f"{dog.city}"

    id_data = [
        [Paragraph("Canine Name:", cell_label), Paragraph(f"<b>{dog.name}</b>", cell_val), Paragraph("Registry Status:", cell_label), Paragraph(dog.get_approval_status_display(), cell_val)],
        [Paragraph("Breed Heritage:", cell_label), Paragraph(breed_desc, cell_val), Paragraph("Kennel Club (KCI):", cell_label), Paragraph(kci_text, cell_val)],
        [Paragraph("Gender / Role:", cell_label), Paragraph(gender_text, cell_val), Paragraph("Chronological Age:", cell_label), Paragraph(age_text, cell_val)],
        [Paragraph("Weight & Build:", cell_label), Paragraph(weight_text, cell_val), Paragraph("Locality:", cell_label), Paragraph(location_text, cell_val)],
    ]

    id_table = Table(id_data, colWidths=[1.5*inch, 2.3*inch, 1.4*inch, 2.2*inch])
    id_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(id_table)
    story.append(Spacer(1, 14))

    # Section 2: Veterinary Health & Screening
    story.append(Paragraph("2. VETERINARY HEALTH & IMMUNIZATION SCREENING", section_heading))
    
    vac_status = "Fully Immunized (Rabies + Core DHPPiL)" if dog.is_vaccinated else "Pending Update"
    bruc_status = "Negative / Cleared" if dog.has_brucellosis_clearance else "Not Yet Screened"
    deworm_status = dog.last_deworming_date.strftime("%b %d, %Y") if dog.last_deworming_date else "Not Recorded"
    med_notes = dog.medical_history if dog.medical_history else "No chronic ailments or genetic disorders reported."

    health_data = [
        [Paragraph("Core Vaccinations:", cell_label), Paragraph(vac_status, cell_val), Paragraph("Brucellosis Screening:", cell_label), Paragraph(bruc_status, cell_val)],
        [Paragraph("Last Deworming Date:", cell_label), Paragraph(deworm_status, cell_val), Paragraph("Vaccination Document:", cell_label), Paragraph("Uploaded on File" if dog.vaccination_record else "Self-Certified", cell_val)],
        [Paragraph("Medical Notes:", cell_label), Paragraph(med_notes[:250], cell_val), Paragraph("Breeding Maturity:", cell_label), Paragraph("18+ Months (Compliant)" if dog.is_breeding_age else "Junior / Underage (<18 Mo)", cell_val)],
    ]

    health_table = Table(health_data, colWidths=[1.5*inch, 2.3*inch, 1.4*inch, 2.2*inch])
    health_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(health_table)
    story.append(Spacer(1, 14))

    # Section 3: Mating Terms & Behavioral Profile
    story.append(Paragraph("3. ETHICAL MATING TERMS & TEMPERAMENT", section_heading))
    
    stud_fee_text = f"INR {dog.stud_fee_amount:,.2f}" if dog.stud_fee_amount else "N/A"
    terms_text = dog.get_mating_terms_display() if hasattr(dog, 'get_mating_terms_display') else dog.mating_terms

    behavior_desc = f"Dog Friendliness: {dog.dog_friendly_rating}/5 · Human Friendliness: {dog.human_friendly_rating}/5 · Energy: {dog.energy_level_rating}/5"

    mating_data = [
        [Paragraph("Availability Status:", cell_label), Paragraph("Active / Available" if dog.is_available else "Resting / Private", cell_val), Paragraph("Mating Terms:", cell_label), Paragraph(terms_text, cell_val)],
        [Paragraph("Expected Stud Fee:", cell_label), Paragraph(stud_fee_text, cell_val), Paragraph("Previous Litters:", cell_label), Paragraph(str(dog.previous_litters), cell_val)],
        [Paragraph("Shelter / Provider:", cell_label), Paragraph(dog.get_shelter_provider_display(), cell_val), Paragraph("Travel Range:", cell_label), Paragraph(dog.get_travel_range_display(), cell_val)],
        [Paragraph("Behavior Scores:", cell_label), Paragraph(behavior_desc, cell_val), Paragraph("Lineage Record:", cell_label), Paragraph(dog.lineage_details[:100] if dog.lineage_details else "Standard Verified Lineage", cell_val)],
    ]

    mating_table = Table(mating_data, colWidths=[1.5*inch, 2.3*inch, 1.4*inch, 2.2*inch])
    mating_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(mating_table)
    story.append(Spacer(1, 14))

    # Section 4: Owner & Authentication Footer
    story.append(Paragraph("4. REGISTERED OWNER & CERTIFICATION SIGN-OFF", section_heading))
    owner_data = [
        [Paragraph("Registered Owner:", cell_label), Paragraph(dog.owner.username, cell_val), Paragraph("Issue Date:", cell_label), Paragraph(datetime.now().strftime("%B %d, %Y"), cell_val)],
        [Paragraph("Platform:", cell_label), Paragraph("K9Match Ethical Canine Breeding Network", cell_val), Paragraph("Verification Seal:", cell_label), Paragraph("AUTHENTICATED PASSPORT", cell_val)],
    ]
    owner_table = Table(owner_data, colWidths=[1.5*inch, 2.3*inch, 1.4*inch, 2.2*inch])
    owner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#86efac")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(owner_table)
    story.append(Spacer(1, 16))

    # Welfare note
    footer_text = Paragraph(
        "<i>Notice: This official canine passport is generated by K9Match. All registered dogs must abide by the 4-Point Canine Welfare Charter, strictly prohibiting underage mating (<18 months), commercial mill operations, and unverified pedigrees.</i>",
        subtitle_style
    )
    story.append(footer_text)

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_breeding_contract_pdf(match, custom_data=None):
    """
    Generates a legally structured, professional Canine Breeding & Stud Service Agreement PDF
    binding both canine owners to agreed financial terms, health warranties, and ethical mating covenants.
    """
    custom_data = custom_data or {}
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Colors
    primary_color = colors.HexColor("#004ac6")
    secondary_color = colors.HexColor("#006242")
    dark_color = colors.HexColor("#0f172a")
    gray_color = colors.HexColor("#64748b")
    light_bg = colors.HexColor("#f8fafc")
    gold_color = colors.HexColor("#b45309")
    border_color = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        alignment=1
    )

    subtitle_style = ParagraphStyle(
        'ContractSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=gray_color,
        alignment=1
    )

    section_heading = ParagraphStyle(
        'ContractSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4
    )

    cell_label = ParagraphStyle(
        'ContractCellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=dark_color
    )

    cell_val = ParagraphStyle(
        'ContractCellVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=dark_color
    )

    legal_text_style = ParagraphStyle(
        'ContractLegalText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=dark_color
    )

    # Determine Sire (Male) and Dam (Female)
    sender_dog = match.sender_dog
    target_dog = match.target_dog

    if sender_dog and sender_dog.gender.lower() == 'male':
        sire_dog = sender_dog
        sire_owner = match.sender
        dam_dog = target_dog
        dam_owner = match.receiver
    elif target_dog and target_dog.gender.lower() == 'male':
        sire_dog = target_dog
        sire_owner = match.receiver
        dam_dog = sender_dog
        dam_owner = match.sender
    else:
        # Fallback if both genders not distinct
        sire_dog = sender_dog or target_dog
        sire_owner = match.sender
        dam_dog = target_dog or sender_dog
        dam_owner = match.receiver

    story = []

    # Contract Header
    contract_id = f"K9M-AGR-{match.id:05d}"
    agreement_date = custom_data.get('agreement_date') or datetime.now().strftime("%B %d, %Y")

    story.append(Paragraph("CANINE BREEDING & STUD SERVICE AGREEMENT", title_style))
    story.append(Paragraph(
        f"K9Match Verified Breeding Contract · Contract Reference: <b>{contract_id}</b> · Date: <b>{agreement_date}</b>",
        subtitle_style
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=8))

    # Preamble
    sire_owner_name = sire_owner.get_full_name() or sire_owner.username
    dam_owner_name = dam_owner.get_full_name() or dam_owner.username
    preamble_text = (
        f"This legally structured Canine Breeding & Stud Service Agreement is entered into on <b>{agreement_date}</b> by and between "
        f"<b>{sire_owner_name}</b> (hereinafter referred to as the <i>'Sire Owner'</i>) and "
        f"<b>{dam_owner_name}</b> (hereinafter referred to as the <i>'Dam Owner'</i>) through the K9Match Ethical Canine Matchmaking Platform. "
        "Both parties mutually agree to the terms, warranties, and obligations set forth herein."
    )
    story.append(Paragraph(preamble_text, legal_text_style))
    story.append(Spacer(1, 8))

    # Section 1: Canine Parties Identification
    story.append(Paragraph("1. IDENTIFICATION OF SIRE & DAM", section_heading))

    sire_kci = f"KCI #{sire_dog.kci_number}" if (sire_dog and sire_dog.kci_registered and sire_dog.kci_number) else ("KCI Registered" if (sire_dog and sire_dog.kci_registered) else "Pedigree Record Pending")
    dam_kci = f"KCI #{dam_dog.kci_number}" if (dam_dog and dam_dog.kci_registered and dam_dog.kci_number) else ("KCI Registered" if (dam_dog and dam_dog.kci_registered) else "Pedigree Record Pending")
    
    sire_name = sire_dog.name if sire_dog else "N/A"
    dam_name = dam_dog.name if dam_dog else "N/A"
    sire_breed = sire_dog.breed if sire_dog else "N/A"
    dam_breed = dam_dog.breed if dam_dog else "N/A"
    sire_age = f"{sire_dog.age_years}y {sire_dog.age_months}m" if sire_dog else "N/A"
    dam_age = f"{dam_dog.age_years}y {dam_dog.age_months}m" if dam_dog else "N/A"
    sire_city = sire_dog.city if sire_dog else "N/A"
    dam_city = dam_dog.city if dam_dog else "N/A"

    canine_table_data = [
        [
            Paragraph("<b>SIRE (MALE CANINE)</b>", cell_label),
            Paragraph("<b>DETAILS</b>", cell_label),
            Paragraph("<b>DAM (FEMALE CANINE)</b>", cell_label),
            Paragraph("<b>DETAILS</b>", cell_label),
        ],
        [
            Paragraph("Canine Name:", cell_label), Paragraph(sire_name, cell_val),
            Paragraph("Canine Name:", cell_label), Paragraph(dam_name, cell_val),
        ],
        [
            Paragraph("Breed:", cell_label), Paragraph(sire_breed, cell_val),
            Paragraph("Breed:", cell_label), Paragraph(dam_breed, cell_val),
        ],
        [
            Paragraph("Age / Location:", cell_label), Paragraph(f"{sire_age} · {sire_city}", cell_val),
            Paragraph("Age / Location:", cell_label), Paragraph(f"{dam_age} · {dam_city}", cell_val),
        ],
        [
            Paragraph("Registry:", cell_label), Paragraph(sire_kci, cell_val),
            Paragraph("Registry:", cell_label), Paragraph(dam_kci, cell_val),
        ],
        [
            Paragraph("Owner Name:", cell_label), Paragraph(f"{sire_owner_name} ({sire_owner.username})", cell_val),
            Paragraph("Owner Name:", cell_label), Paragraph(f"{dam_owner_name} ({dam_owner.username})", cell_val),
        ],
        [
            Paragraph("Owner Contact:", cell_label), Paragraph(f"{sire_owner.phone_number or sire_owner.email}", cell_val),
            Paragraph("Owner Contact:", cell_label), Paragraph(f"{dam_owner.phone_number or dam_owner.email}", cell_val),
        ],
    ]

    canine_table = Table(canine_table_data, colWidths=[1.3*inch, 2.4*inch, 1.3*inch, 2.4*inch])
    canine_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e7eeff")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(canine_table)
    story.append(Spacer(1, 8))

    # Section 2: Compensation & Mating Terms
    story.append(Paragraph("2. MATING TERMS & FINANCIAL COMPENSATION", section_heading))

    fee_type = custom_data.get('mating_terms') or (sire_dog.get_mating_terms_display() if sire_dog else "Negotiated")
    fee_amount = custom_data.get('stud_fee_amount') or (f"₹ {sire_dog.stud_fee_amount:,}" if (sire_dog and sire_dog.stud_fee_amount) else "Mutually Agreed")
    payment_schedule = custom_data.get('payment_schedule') or "50% due on first successful natural mating tie; remaining 50% due on veterinary ultrasound confirmation of pregnancy (at Day 30)."
    pick_of_litter = custom_data.get('pick_of_litter_terms') or "Sire owner is entitled to first selection of the litter (Pick of Litter) at 45 days of age, provided a minimum of two (2) surviving puppies are whelped."

    terms_data = [
        [Paragraph("Agreed Terms Type:", cell_label), Paragraph(str(fee_type), cell_val)],
        [Paragraph("Agreed Stud Fee:", cell_label), Paragraph(str(fee_amount), cell_val)],
        [Paragraph("Payment Schedule:", cell_label), Paragraph(str(payment_schedule), cell_val)],
        [Paragraph("Pick of Litter Terms:", cell_label), Paragraph(str(pick_of_litter), cell_val)],
    ]

    terms_table = Table(terms_data, colWidths=[1.8*inch, 5.6*inch])
    terms_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(terms_table)
    story.append(Spacer(1, 8))

    # Section 3: Logistics & Health Clearances
    story.append(Paragraph("3. LOGISTICS, METHOD & VETERINARY HEALTH COVENANTS", section_heading))

    mating_dates = custom_data.get('mating_dates') or "Optimal estrus window (estimated Days 10–14 of female heat cycle)"
    mating_location = custom_data.get('mating_location') or (f"{sire_dog.city} (Sire's residence or designated Veterinary Clinic)" if sire_dog else "Mutually Agreed Location")
    mating_method = custom_data.get('mating_method') or "Supervised Natural Mating (or Transcervical/Artificial Insemination by licensed vet)"
    repeat_policy = custom_data.get('repeat_mating_guarantee') or "YES. If the Dam fails to conceive (as verified by licensed vet ultrasound at 30 days post-mating), the Sire owner guarantees one (1) complimentary repeat service on her next heat cycle."

    logistics_data = [
        [Paragraph("Planned Dates:", cell_label), Paragraph(str(mating_dates), cell_val)],
        [Paragraph("Planned Location:", cell_label), Paragraph(str(mating_location), cell_val)],
        [Paragraph("Mating Method:", cell_label), Paragraph(str(mating_method), cell_val)],
        [Paragraph("Repeat Service Policy:", cell_label), Paragraph(str(repeat_policy), cell_val)],
        [Paragraph("Health Warranties:", cell_label), Paragraph(
            "Both parties warrant that both canines are in sound health, free from infectious or contagious diseases, "
            "up to date on core vaccinations (Rabies, DHPPiL), certified Canine Brucellosis negative, and free from transmissible venereal tumors (TVT).",
            cell_val
        )],
    ]

    logistics_table = Table(logistics_data, colWidths=[1.8*inch, 5.6*inch])
    logistics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(logistics_table)
    story.append(Spacer(1, 8))

    # Special Conditions
    special_notes = custom_data.get('special_conditions') or "Both parties agree to treat both animals humanely, avoid excessive breeding ties, and register all resulting puppies in accordance with Kennel Club rules."
    story.append(Paragraph("4. SPECIAL CONDITIONS & ETHICAL COVENANTS", section_heading))
    story.append(Paragraph(f"<i>{special_notes}</i>", legal_text_style))
    story.append(Spacer(1, 10))

    # Section 5: Signature Blocks
    story.append(Paragraph("5. EXECUTION & SIGNATURES", section_heading))

    sig_data = [
        [
            Paragraph("<b>SIRE OWNER SIGNATURE</b>", cell_label),
            Paragraph("<b>DAM OWNER SIGNATURE</b>", cell_label),
        ],
        [
            Paragraph(f"Full Name: <b>{sire_owner_name}</b>", cell_val),
            Paragraph(f"Full Name: <b>{dam_owner_name}</b>", cell_val),
        ],
        [
            Paragraph(f"Date: {agreement_date}", cell_val),
            Paragraph(f"Date: {agreement_date}", cell_val),
        ],
        [
            Paragraph("<br/><br/>________________________________________<br/>Signature", cell_val),
            Paragraph("<br/><br/>________________________________________<br/>Signature", cell_val),
        ],
    ]

    sig_table = Table(sig_data, colWidths=[3.7*inch, 3.7*inch])
    sig_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#86efac")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 8))

    # Footer note
    footer_text = Paragraph(
        "<i>Notice: This official agreement is executed through K9Match. Both parties acknowledge compliance with the Prevention of Cruelty to Animals (Dog Breeding and Marketing) Rules and ethical breeding standards.</i>",
        subtitle_style
    )
    story.append(footer_text)

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
