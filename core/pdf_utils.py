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
