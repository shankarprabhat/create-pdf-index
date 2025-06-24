# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 21:01:00 2025

@author: Admin
"""

import json

def build_toc(headings_data):
    # Filter out heading_level 0 as they appear to be page/document metadata
    # Also create a map for quick lookup by node_id for parent/child linking
    heading_map = {h['node_id']: h for h in headings_data if h.get('heading_level') != 0}

    # Initialize a structure for the TOC (e.g., a list of dictionaries)
    toc = []

    # Identify true top-level sections (heading_level 1 with no meaningful parent in the TOC)
    # We explicitly check that the parent (if it exists) is NOT a level 0 heading.
    top_level_headings = []
    for h in heading_map.values():
        if h['heading_level'] == 1:
            parent_id = h.get('parent_node_id')
            if parent_id is None: # Truly no parent, definitely a top-level
                top_level_headings.append(h)
            else:
                parent_heading = heading_map.get(parent_id)
                # If parent exists and is NOT level 0, then this is a subsection of that parent.
                # If parent is level 0, we treat this current heading as a top-level.
                if parent_heading and parent_heading.get('heading_level') != 0:
                    # This heading has a valid, non-zero-level parent, so it's not a top-level for our TOC
                    continue
                else:
                    top_level_headings.append(h)


    # Sort top-level headings by page_label and then by their original order (approximate)
    # Using 'heading_id' for secondary sort if it's numerical and sequential
    top_level_headings.sort(key=lambda x: (int(x.get('page_label', 0)), x.get('heading_id', '')))

    for top_heading in top_level_headings:
        toc.append(parse_section(top_heading, heading_map))
    return toc

def parse_section(current_heading, heading_map):
    section_entry = {
        "title": current_heading["section_title"],
        "page": current_heading["page_label"],
        "level": current_heading["heading_level"],
        "subsections": []
    }

    # Find children (subsections) of the current heading
    # Children will have a heading_level one greater than the parent
    # and their parent_node_id will match the current heading's node_id.
    children = [
        h for h in heading_map.values()
        if h.get('parent_node_id') == current_heading['node_id'] and
           h.get('heading_level') == current_heading['heading_level'] + 1
    ]

    # Sort children to maintain order
    children.sort(key=lambda x: (int(x.get('page_label', 0)), x.get('heading_id', ''))) # Sort by page and heading_id

    for child in children:
        section_entry["subsections"].append(parse_section(child, heading_map))

    return section_entry

def print_toc(toc_list, indent_level=0):
    for entry in toc_list:
        # Use an appropriate symbol or just indentation
        prefix = "  " * indent_level
        print(f"{prefix}{entry['title']} (Page: {entry['page']})")
        if entry["subsections"]:
            print_toc(entry["subsections"], indent_level + 1)

# Your provided JSON data
json_data = [
    {
        "section_title": "30 Churchill Place ● Canary Wharf ● London E14 5EU ● United Kingdom",
        "page_label": "1",
        "heading_level": 1,
        "heading_id": "30",
        "parent_node_id": None,
        "node_id": "876ce1f5-dc99-48e4-a973-ea2472587a10",
        "content": "An agency of the European Union     \nTelephone +44 (0)20 3660 6000 Facsimile +44 (0)20 3660 5555 \nSend a question via our website www.ema.europa.eu/contact \n \n \n© European Medicines Agency, 2018. Reproduction is authorised provided the source is acknowledged."
    },
    {
        "section_title": "1 December 2016",
        "page_label": "1",
        "heading_level": 1,
        "heading_id": "1",
        "parent_node_id": None,
        "node_id": "b437be53-ebbd-438b-b55f-b715ef6c3faa",
        "content": "EMA/CHMP/ICH/135/1995 \nCommittee for Human Medicinal Products \nGuideline for good clinical practice E6(R2) \nStep 5 \nAdopted by CHMP for release for consultation 23 July 2015 \nStart of public consultation  4 August 2015 \nEnd of consultation (deadline for comments)  3 February 2016 \nFinal adoption by CHMP 15 December 2016 \nDate for coming into effect 14 June 2017"
    },
    {
        "section_title": "Document Preamble",
        "page_label": "2",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "a30a2e8b-5fee-41b2-a489-6d6ad1a2df1e",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 2/68 \n \n \nDocument History \n \nFirst \nCodification History Date \nNew \nCodification \nNovember"
    },
    {
        "section_title": "2005 \nE6 Approval by the CPMP under Step 3 and release for",
        "page_label": "2",
        "heading_level": 1,
        "heading_id": "2005",
        "parent_node_id": "a30a2e8b-5fee-41b2-a489-6d6ad1a2df1e",
        "node_id": "8665151d-9f42-4f8b-8862-619e25517e02",
        "content": "public consultation. \nMay 1995 E6 \nE6 Approval by the CPMP under Step 4 and released for \ninformation. \nJuly 1996 E6 \nStep 5 corrected version \nE6 Approval by the CPMP of Post-Step 4 editorial \ncorrections. \nJuly 2002 E6(R1) \nCurrent E6(R2) Addendum Step 5 version \nCode History Date \nE6 Adoption by the Regulatory Members of the ICH Assembly under \nStep 4. \nIntegrated Addendum to ICH E6(R1) document. Changes are \nintegrated directly into the following sections of the parental \nGuideline: Introduction, 1.63, 1.64, 1.65, 2.10, 2.13, 4.2.5, 4.2.6, \n4.9.0, 5.0, 5.0.1, 5.0.2, 5.0.3, 5.0.4, 5.0.5, 5.0.6, 5.0.7, 5.2.2,"
    },
    {
        "section_title": "Full Document Content",
        "page_label": "3",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "78a835b2-af00-4405-843f-262e8ca81362",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 3/68 \n \n \nGuideline for good clinical practice E6(R2) \nTable of contents \nIntroduction ................................................................................................ 6 \n1. Glossary .................................................................................................. 7 \n2. The principles of ICH GCP ...................................................................... 15 \n3. Institutional Review Board / Independent Ethics Committee (IRB/IEC)\n .................................................................................................................. 16 \n3.1. Responsibilities .................................................................................................. 16 \n3.2. Composition, Functions and Operations ................................................................. 18 \n3.3. Procedures ........................................................................................................ 18 \n3.4. Records ............................................................................................................. 20 \n4. Investigator .......................................................................................... 20 \n4.1. Investigator's Qualifications and Agreements ......................................................... 20 \n4.2. Adequate Resources ........................................................................................... 20 \n4.3. Medical Care of Trial Subjects .............................................................................. 21 \n4.4. Communication with IRB/IEC ............................................................................... 22 \n4.5. Compliance with Protocol .................................................................................... 22 \n4.6. Investigational Product(s) ................................................................................... 23 \n4.7. Randomization Procedures and Unblinding ............................................................. 24 \n4.8. Informed Consent of Trial Subjects ....................................................................... 24 \n4.9. Records and Reports ........................................................................................... 27 \n4.10. Progress Reports .............................................................................................. 29 \n4.11. Safety Reporting .............................................................................................. 29 \n4.12. Premature Termination or Suspension of a Trial.................................................... 29 \n4.13. Final Report(s) by Investigator ........................................................................... 30 \n5. Sponsor ................................................................................................. 30 \n5.0. Quality management .......................................................................................... 30 \n5.1. Quality assurance and quality control .................................................................... 31 \n5.2. Contract Research Organization (CRO) .................................................................. 32 \n5.3. Medical expertise ............................................................................................... 32 \n5.4. Trial design........................................................................................................ 33 \n5.5. Trial management, data handling, and record keeping ............................................ 33 \n5.6. Investigator selection.......................................................................................... 35 \n5.7. Allocation of responsibilities ................................................................................. 36 \n5.8. Compensation to subjects and investigators .......................................................... 36 \n5.9. Financing .......................................................................................................... 36 \n5.10. Notification/submission to regulatory authority(ies) .............................................. 36 \n5.11. Confirmation of review by IRB/IEC ...................................................................... 36 \n5.12. Information on investigational product(s) ............................................................ 37 \n5.13. Manufacturing, packaging, labelling, and coding investigational product(s)  .............. 37 \n5.14. Supplying and handling investigational product(s) ................................................ 38"
    },
    {
        "section_title": "Full Document Content",
        "page_label": "4",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "f87c16bf-ebd3-4be4-8e3b-9b3863b0341b",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 4/68 \n \n \n5.15. Record access .................................................................................                 39 \n5.16. Safety information .................................................................................           39 \n5.17. Adverse drug reaction reporting .................................................................        39 \n5.18. Monitoring .................................................................................................      40 \n5.18.1. Purpose .................................................................................................       40 \n5.18.2. Selection and qualifications of monitors .................................................          40 \n5.18.3. Extent and nature of monitoring .................................................................      40 \n5.18.4. Monitor's responsibilities .............................................................................. 41 \n5.18.5. Monitoring procedures ................................................................................... 43 \n5.18.6. Monitoring report .......................................................................................... 43 \n5.18.7. Monitoring plan ............................................................................................ 43 \n5.19. Audit .................................................................................................             43 \n5.19.1. Purpose .................................................................................................       43 \n5.19.2. Selection and qualification of auditors .................................................            44 \n5.19.3. Auditing procedures .................................................................................      44 \n5.20. Noncompliance .................................................................................              44 \n5.21. Premature termination or suspension of a trial ................................................... 44 \n5.22. Clinical trial/study reports ............................................................................... 45 \n5.23. Multicentre trials .................................................................................          45 \n6. Clinical trial protocol and protocol amendment(s) ................................. 46 \n6.1. General Information .................................................................................         46 \n6.2. Background Information ................................................................................     46 \n6.3. Trial objectives and purpose ............................................................................   47 \n6.4. Trial design...................................................................................................   47 \n6.5. Selection and withdrawal of subjects...............................................................     48 \n6.6. Treatment of Subjects....................................................................................    49 \n6.7. Assessment of Efficacy ..................................................................................   49 \n6.8. Assessment of Safety ....................................................................................    49 \n6.9. Statistics .................................................................................................      50 \n6.10. Direct access to source data/documents ..........................................................    50 \n6.11. Quality control and quality assurance ............................................................      50 \n6.12. Ethics ........................................................................................................   50 \n6.13. Data handling and record keeping....................................................................   51 \n6.14. Financing and insurance ..............................................................................      51 \n6.15. Publication policy ........................................................................................    51 \n6.16. Supplements .............................................................................................     51 \n7. Investigator’s brochure ......................................................................... 52 \n7.1. Introduction.................................................................................................    52 \n7.2. General considerations .................................................................................    52 \n7.2.1. Title page ...................................................................................................   52 \n7.2.2. Confidentiality statement ............................................................................     53 \n7.3. Contents of the investigator’s brochure ............................................................    53 \n7.3.1. Table of contents ......................................................................................      53 \n7.3.2. Summary ...................................................................................................    53 \n7.3.3. Introduction ...............................................................................................    53"
    },
    {
        "section_title": "Full Document Content",
        "page_label": "5",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "6af2bf0f-58c1-457b-b4d5-c1c2c77efd7c",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 5/68 \n \n \n7.3.4. Physical, chemical, and pharmaceutical properties and formulation ........................ 53 \n7.3.5. Nonclinical studies ........................................................................................... 53 \n7.3.6. Effects in humans ............................................................................................ 55 \n7.3.7. Summary of Data and Guidance for the Investigator ............................................ 56 \n7.4. Appendix 1: ....................................................................................................... 57 \n7.5. Appendix 2: ....................................................................................................... 58 \n8. Essential documents for the conduct of a clinical trial ........................... 59 \n8.1. Introduction....................................................................................................... 59 \n8.2. Before the clinical phase of the trial commences .................................................... 60 \n8.3. During the Clinical Conduct of the Trial .................................................................. 64 \n8.4. After Completion or Termination of the Trial ........................................................... 68"
    },
    {
        "section_title": "Full Document Content",
        "page_label": "6",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "8f215ee3-01f4-464a-9f1c-72fe01efaf9d",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 6/68 \n \n \nIntroduction \nGood Clinical Practice (GCP) is an international ethical and scientific quality standard for designing, \nconducting, recording and reporting trials that involve the participation of human subjects. Compliance \nwith this standard provides public assurance that the rights, safety and well-being of trial subjects are \nprotected, consistent with the principles that have their origin in the Declaration of Helsinki, and that \nthe clinical trial data are credible. \nThe objective of this ICH GCP Guideline is to provide a unified standard for the European Union (EU), \nJapan and the United States to facilitate the mutual acceptance of clinical data by the regulatory \nauthorities in these jurisdictions. \nThe guideline was developed with consideration of the current good clinical practices of the European \nUnion, Japan, and the United States, as well as those of Australia, Canada, the Nordic countries and \nthe World Health Organization (WHO). \nThis guideline should be followed when generating clinical trial data that are intended to be submitted \nto regulatory authorities. \nThe principles established in this guideline may also be applied to other clinical investigations that may \nhave an impact on the safety and well-being of human subjects. \nADDENDUM \nSince the development of the ICH GCP Guideline, the scale, complexity, and cost of clinical trials have \nincreased. Evolutions in technology and risk management processes offer new opportunities to \nincrease efficiency and focus on relevant activities. When the original ICH E6(R1) text was prepared, \nclinical trials were performed in a largely paper-based process. Advances in use of electronic data \nrecording and reporting facilitate implementation of other approaches. For example, centralized \nmonitoring can now offer a greater advantage, to a broader range of trials than is suggested in the \noriginal text. Therefore, this guideline has been amended to encourage implementation of improved \nand more efficient approaches to clinical trial design, conduct, oversight, recording and reporting while \ncontinuing to ensure human subject protection and reliability of trial results. Standards regarding \nelectronic records and essential documents intended to increase clinical trial quality and efficiency have \nalso been updated. \nThis guideline should be read in conjunction with other ICH guidelines relevant to the conduct of \nclinical trials (e.g., E2A (clinical safety data management), E3 (clinical study reporting), E7 (geriatric \npopulations), E8 (general considerations for clinical trials), E9 (statistical principles), and E11 (pediatric \npopulations)). \nThis ICH GCP Guideline Integrated Addendum provides a unified standard for the European Union, \nJapan, the United States, Canada, and Switzerland to facilitate the mutual acceptance of data from \nclinical trials by the regulatory authorities in these jurisdictions. In the event of any conflict between \nthe E6(R1) text and the E6(R2) addendum text, the E6(R2) addendum text should take priority."
    },
    {
        "section_title": "Full Document Content",
        "page_label": "7",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "4f4613b1-c787-43ce-8916-9462a4394201",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 7/68 \n \n \n1.  Glossary \n1.1.  Adverse Drug Reaction (ADR) \nIn the pre-approval clinical experience with a new medicinal product or its new usages, particularly as \nthe therapeutic dose(s) may not be established: all noxious and unintended responses to a medicinal \nproduct related to any dose should be considered adverse drug reactions. The phrase responses to a \nmedicinal product means that a causal relationship between a medicinal product and an adverse event \nis at least a reasonable possibility, i.e. the relationship cannot be ruled out. \nRegarding marketed medicinal products: a response to a drug which is noxious and unintended and \nwhich occurs at doses normally used in man for prophylaxis, diagnosis, or therapy of diseases or for \nmodification of physiological function (see the ICH Guideline for Clinical Safety Data Management: \nDefinitions and Standards for Expedited Reporting). \n1.2.  Adverse Event (AE) \nAny untoward medical occurrence in a patient or clinical investigation subject administered a \npharmaceutical product and which does not necessarily have a causal relationship with this treatment. \nAn adverse event (AE) can therefore be any unfavourable and unintended sign (including an abnormal \nlaboratory finding), symptom, or disease temporally associated with the use of a medicinal \n(investigational) product, whether or not related to the medicinal (investigational) product (see the \nICH Guideline for Clinical Safety Data Management: Definitions and Standards for Expedited \nReporting). \n1.3.  Amendment (to the protocol) \nSee Protocol Amendment. \n1.4.  Applicable regulatory requirement(s) \nAny law(s) and regulation(s) addressing the conduct of clinical trials of investigational products. \n1.5.  Approval (in relation to institutional review boards) \nThe affirmative decision of the IRB that the clinical trial has been reviewed and may be conducted at \nthe institution site within the constraints set forth by the IRB, the institution, Good Clinical Practice \n(GCP), and the applicable regulatory requirements. \n1.6.  Audit \nA systematic and independent examination of trial related activities and documents to determine \nwhether the evaluated trial related activities were conducted, and the data were recorded, analyzed \nand accurately reported according to the protocol, sponsor's standard operating procedures (SOPs), \nGood Clinical Practice (GCP), and the applicable regulatory requirement(s). \n1.7.  Audit certificate \nA declaration of confirmation by the auditor that an audit has taken place."
    },
    {
        "section_title": "Full Document Content",
        "page_label": "8",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "b98edc31-941a-462f-8396-e9d37b88edf0",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 8/68 \n \n \n1.8.  Audit report \nA written evaluation by the sponsor's auditor of the results of the audit. \n1.9.   Audit trail \nDocumentation that allows reconstruction of the course of events.  \n1.10.  Blinding/masking \nA procedure in which one or more parties to the trial are kept unaware of the treatment assignment(s). \nSingle-blinding usually refers to the subject(s) being unaware, and double-blinding usually refers to \nthe subject(s), investigator(s), monitor, and, in some cases, data analyst(s) being unaware of the \ntreatment assignment(s). \n1.11.  Case Report Form (CRF) \nA printed, optical, or electronic document designed to record all of the protocol required information to \nbe reported to the sponsor on each trial subject. \n1.12.  Clinical trial/study \nAny investigation in human subjects intended to discover or verify the clinical, pharmacological and/or \nother pharmacodynamic effects of an investigational product(s), and/or to identify any adverse \nreactions to an investigational product(s), and/or to study absorption, distribution, metabolism, and \nexcretion of an investigational product(s) with the object of ascertaining its safety and/or efficacy. The \nterms clinical trial and clinical study are synonymous. \n1.13.  Clinical trial/study report \nA written description of a trial/study of any therapeutic, prophylactic, or diagnostic agent conducted in \nhuman subjects, in which the clinical and statistical description, presentations, and analyses are fully \nintegrated into a single report (see the ICH Guideline for Structure and Content of Clinical Study \nReports). \n1.14.  Comparator (Product) \nAn investigational or marketed product (i.e., active control), or placebo, used as a reference in a \nclinical trial. \n1.15.  Compliance (in relation to trials) \nAdherence to all the trial-related requirements, Good Clinical Practice (GCP)requirements, and the \napplicable regulatory requirements. \n1.16.  Confidentiality \nPrevention of disclosure, to other than authorized individuals, of a sponsor's proprietary information or \nof a subject's identity."
    },
    {
        "section_title": "Full Document Content",
        "page_label": "9",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "dc676255-1346-40a9-ba0c-aba1743f9954",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 9/68 \n \n \n1.17.  Contract \nA written, dated, and signed agreement between two or more involved parties that sets out any \narrangements on delegation and distribution of tasks and obligations and, if appropriate, on financial \nmatters. The protocol may serve as the basis of a contract. \n1.18.  Coordinating committee \nA committee that a sponsor may organize to coordinate the conduct of a multicentre trial. \n1.19.  Coordinating investigator \nAn investigator assigned the responsibility for the coordination of investigators at different centres \nparticipating in a multicentre trial. \n1.20.  Contract Research Organization (CRO) \nA person or an organization (commercial, academic, or other) contracted by the sponsor to perform \none or more of a sponsor's trial-related duties and functions. \n1.21.  Direct access \nPermission to examine, analyze, verify, and reproduce any records and reports that are important to \nevaluation of a clinical trial. Any party (e.g., domestic and foreign regulatory authorities, sponsor's \nmonitors and auditors) with direct access should take all reasonable precautions within the constraints \nof the applicable regulatory requirement(s) to maintain the confidentiality of subjects' identities and \nsponsor’s proprietary information. \n1.22.  Documentation \nAll records, in any form (including, but not limited to, written, electronic, magnetic, and optical \nrecords, and scans, x-rays, and electrocardiograms) that describe or record the methods, conduct, \nand/or results of a trial, the factors affecting a trial, and the actions taken. \n1.23.  Essential documents \nDocuments which individually and collectively permit evaluation of the conduct of a study and the \nquality of the data produced (see 8. Essential Documents for the Conduct of a Clinical Trial). \n1.24.  Good Clinical Practice (GCP) \nA standard for the design, conduct, performance, monitoring, auditing, recording, analyses, and \nreporting of clinical trials that provides assurance that the data and reported results are credible and \naccurate, and that the rights, integrity, and confidentiality of trial subjects are protected. \n1.25.  Independent Data-Monitoring Committee (IDMC) (data and safety \nmonitoring board, monitoring committee, data monitoring committee) \nAn independent data-monitoring committee that may be established by the sponsor to assess at \nintervals the progress of a clinical trial, the safety data, and the critical efficacy endpoints, and to \nrecommend to the sponsor whether to continue, modify, or stop a trial."
    },
    {
        "section_title": "Full Document Content",
        "page_label": "10",
        "heading_level": 0,
        "heading_id": "",
        "parent_node_id": None,
        "node_id": "1df6932c-899c-4bcd-8ef1-fbbb1a8b52be",
        "content": "Guideline for good clinical practice E6(R2)   \nEMA/CHMP/ICH/135/1995  Page 10/68 \n \n \n1.26.  Impartial witness \nA person, who is independent of the trial, who cannot be unfairly influenced by people involved with \nthe trial, who attends the informed consent process if the subject or the subject’s legally acceptable \nrepresentative cannot read, and who reads the informed consent form and any other written \ninformation supplied to the subject. \n1.27.  Independent Ethics Committee (IEC) \nAn independent body (a review board or a committee, institutional, regional, national, or \nsupranational), constituted of medical professionals and non-medical members, whose responsibility it \nis to ensure the protection of the rights, safety and well-being of human subjects involved in a trial and \nto provide public assurance of that protection, by, among other things, reviewing and approving / \nproviding favourable opinion on, the trial protocol, the suitability of the investigator(s), facilities, and \nthe methods and material to be used in obtaining and documenting informed consent of the trial \nsubjects. \nThe legal status, composition, function, operations and regulatory requirements pertaining to \nIndependent Ethics Committees may differ among countries, but should allow the Independent Ethics \nCommittee to act in agreement with GCP as described in this guideline. \n1.28.  Informed consent \nA process by which a subject voluntarily confirms his or her willingness to participate in a particular \ntrial, after having been informed of all aspects of the trial that are relevant to the subject's decision to \nparticipate. Informed consent is documented by means of a written, signed and dated informed \nconsent form. \n1.29.  Inspection \nThe act by a regulatory authority(ies) of conducting an official review of documents, facilities, records, \nand any other resources that are deemed by the authority(ies) to be related to the clinical trial and \nthat may be located at the site of the trial, at the sponsor's and/or contract research organization’s \n(CRO’s) facilities, or at other establishments deemed appropriate by the regulatory authority(ies). \n1.30.  Institution (medical) \nAny public or private entity or agency or medical or dental facility where clinical trials are conducted. \n1.31.  Institutional Review Board (IRB) \nAn independent body constituted of medical, scientific, and non-scientific members, whose \nresponsibility is to ensure the protection of the rights, safety and well-being of human subjects \ninvolved in a trial by, among other things, reviewing, approving, and providing continuing review of \ntrial protocol and amendments and of the methods and material to be used in obtaining and \ndocumenting informed consent of the trial subjects. \n1.32.  Interim clinical trial/study report \nA report of intermediate results and their evaluation based on analyses performed during the course of \na trial."
    }
]

# load the json_data from file
fname = 'extracted_nodes_ich-gcp-r2-step-5.json'
with open(fname, 'r') as f:
    json_data = json.load(f)

# Build the table of contents
table_of_contents = build_toc(json_data)

# Print the table of contents
print("---")
print("Extracted Table of Contents:")
print("---")
print_toc(table_of_contents,3)
print("---")