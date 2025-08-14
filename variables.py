YEARS_SECTIONS = {
        '3': ['A','B', 'C', 'D', 'E'],
        '5': ['A','B', 'C', 'D'],
        '7': ['A', 'B', 'C', 'D']
    }

SUBJECTS_PER_YEAR = {
    '3': {  
        'MATHEMATICS FOR COMPUTER SCIENCE': 5,
        'DIGITAL DESIGN & COMPUTER ORGANIZATION': 4,
        'OPERATING SYSTEM': 3,
        'DATA STRUCTURES & APPLICATIONS': 3,
        'SOCIAL CONNECT & RESPONSIBILITY': 1,
        'OBJECT ORIENTED PROGRAMMING WITH JAVA': 2
    },
    '5': { 
        'SOFTWARE ENGINERING & PROJECT MANAGEMENT': 4,
        'COMPUTER NETWORKS': 5,
        'THEORY OF COMPUTATION': 4,
        'ARTIFICIAL INTELIGENCE': 3,
        'RESEARCH METHODOLOGY & IPR': 4,
        'ENVIRONMENTAL STUDIES AND E-WASTEMANAGEMENT': 3
    },
    '7': {
        'INTERNET OF THINGS': 4,
        'PARALLEL COMPUTING': 4,
        'CRYPTOGRAPHY & NETWORK SECURITY': 3,
        'BIG DATA ANALYTICS': 3
    }
}

# All section-subject pairs assigned to a teacher:
TEACHER_ASSIGNMENTS = {
    'X': [
        ('3A', 'MATHEMATICS FOR COMPUTER SCIENCE'),
        ('3B', 'MATHEMATICS FOR COMPUTER SCIENCE'),
        ('3C', 'MATHEMATICS FOR COMPUTER SCIENCE'),
        ('3D', 'MATHEMATICS FOR COMPUTER SCIENCE'),
        ('3E', 'MATHEMATICS FOR COMPUTER SCIENCE'),
        ('3F', 'MATHEMATICS FOR COMPUTER SCIENCE'),
    ],
    'SHWETHA K R': [
        ('3A', 'DIGITAL DESIGN & COMPUTER ORGANIZATION'),
        ('3A', 'SOCIAL CONNECT & RESPONSIBILITY'),
        ('3B', 'SOCIAL CONNECT & RESPONSIBILITY'),
        ('7A', 'PARALLEL COMPUTING')
    ],
    'VIJAYALAKSHMI M M':[
        ('3A', 'OPERATING SYSTEM'),
        ('3A', 'OBJECT ORIENTED VI PROGRAMMING WITH JAVA'),
        ('7B', 'BIG DATA ANALYTICS')
    ],
    'SUPRIYA':[
        ('3A', 'DATA STRUCTURES & APPLICATIONS'),
        ('5A', 'SOFTWARE ENGINERING & PROJECT MANAGEMENT')
    ],
    'DIVYA G S':[
        ('3B', 'DIGITAL DESIGN & COMPUTER ORGANIZATION'),
        ('5D', 'ARTIFICIAL INTELIGENCE')
    ],
    'GEENA':[
        ('3B', 'OPERATING SYSTEM'),
        ('7C', 'PARALLEL COMPUTING')
    ],
    'PRIYANKA':[
        ('3B', 'DATA STRUCTURES & APPLICATIONS'),
        ('7B', 'CRYPTOGRAPHY & NETWORK SECURITY')
    ],
    'SNIGDHA KESH':[
        ('3C', 'DIGITAL DESIGN & COMPUTER ORGANIZATION'),
        ('7D', 'PARALLEL COMPUTING')
    ],
    'VEENA BHAT':[
        ('3C', 'OPERATING SYSTEM'),
        ('5B', 'ENVIRONMENTAL STUDIES AND E-WASTEMANAGEMENT'),
        ('5D', 'THEORY OF COMPUTATION')
    ],
    'PALLALI KV':[
        ('3C', 'DATA STRUCTURES & APPLICATIONS'),
        ('5C', 'ENVIRONMENTAL STUDIES AND E-WASTEMANAGEMENT'),
        ('5D', 'SOFTWARE ENGINERING & PROJECT MANAGEMENT')
    ],
    'JAYA KARUNA':[
        ('3C', 'SOCIAL CONNECT & RESPONSIBILITY'),
        ('5C', 'RESEARCH METHODOLOGY & IPR'),
        ('7B', 'INTERNET OF THINGS')
    ],
    'PRAVEEN KUMAR B':[
        ('3D', 'DIGITAL DESIGN & COMPUTER ORGANIZATION'),
        ('5B', 'RESEARCH METHODOLOGY & IPR')
    ],
    'RAMYA':[
        ('3D', 'OPERATING SYSTEM'),
        ('7C', 'INTERNET OF THINGS')
    ],
    'KARTHIGA':[
        ('3D', 'DATA STRUCTURES & APPLICATIONS'),
        ('5C', 'SOFTWARE ENGINERING & PROJECT MANAGEMENT')
    ],
    'SHEETAL':[
        ('3D', 'SOCIAL CONNECT & RESPONSIBILITY'),
        ('5B', 'COMPUTER NETWORKS'),
        ('7D', 'CRYPTOGRAPHY & NETWORK SECURITY')
    ],
    'SANGEETHA RAJ':[
        ('3E', 'DIGITAL DESIGN & COMPUTER ORGANIZATION'),
        ('5C', 'COMPUTER NETWORKS')
    ],
    'NIRMALA':[
        ('3E', 'OPERATING SYSTEM'),
        ('5C', 'ARTIFICIAL INTELIGENCE'),
        ('5D', 'ENVIRONMENTAL STUDIES AND E-WASTEMANAGEMENT')
    ],
    'BHAVYA':[
        ('3E', 'DATA STRUCTURES & APPLICATIONS'),
        ('5C', 'THEORY OF COMPUTATION'),
        ('7A', 'CRYPTOGRAPHY & NETWORK SECURITY')
    ],
    'MALA M':[
        ('3E', 'SOCIAL CONNECT & RESPONSIBILITY'),
        ('3B', 'OBJECT ORIENTED PROGRAMMING WITH JAVA'),
        ('5B', 'ARTIFICIAL INTELIGENCE'),
        ('5D', 'RESEARCH METHODOLOGY & IPR')
    ],
    'MAHALAKSHMI B':[
        ('5A', 'COMPUTER NETWORKS'),
        ('7A', 'INTERNET OF THINGS')
    ],
    'VIJAYA NIRMALA':[
        ('5A', 'THEORY OF COMPUTATION'),
        ('7B', 'PARALLEL COMPUTING')
    ],
    'MURALI':[
        ('5A', 'ARTIFICIAL INTELIGENCE'),
        ('3D', 'OBJECT ORIENTED PROGRAMMING WITH JAVA')
    ],
    'RADHA':[
        ('5A', 'RESEARCH METHODOLOGY & IPR'),
        ('3E', 'OBJECT ORIENTED PROGRAMMING WITH JAVA')
    ],
    'RAMESH SHAHABADKAR':[
        ('5A', 'ENVIRONMENTAL STUDIES AND E-WASTEMANAGEMENT'),
        ('7D', 'BIG DATA ANALYTICS')
    ],
    'ANAND KUMAR B':[
        ('5B', 'SOFTWARE ENGINERING & PROJECT MANAGEMENT'),
        ('7C', 'BIG DATA ANALYTICS')
    ],
    'HOD':[
        ('5B', 'THEORY OF COMPUTATION'),
        ('7C', 'CRYPTOGRAPHY & NETWORK SECURITY')
    ],
    'YUVARAJ B N, RABHIRDANATH':[
        ('5D', 'COMPUTER NETWORKS')
    ],
    'R NAGARAJ':[
        ('7A', 'BIG DATA ANALYTICS')
    ],
    'SRINIVASA SETTY':[
        ('7D', 'INTERNET OF THINGS')
    ],
    'PARTHASARATHY':[
        ('3C', 'OBJECT ORIENTED PROGRAMMING WITH JAVA')
    ]
}

PREBOOKED = {
    # 'Teacher1': [(0,0), (2,3)],   # Mon P1, Wed P4 blocked
    # 'Teacher2': [(1,4)],          # Tue P5 blocked
}

LAB_SUBJECTS = {
    '3A': [
        ('DDCO-LAB', 'SHWETHA K R'), 
        ('OS-LAB', 'VIJAYALAKSHMI M M'), 
        ('DSA-LAB', 'SUPRIYA'),
        ('OOPS-LAB', 'VIJAYALAKSHMI M M'),
        ('DV-LAB', 'VIJAYA NIRMALA')
    ],
    '3B': [
        ('DDCO-LAB', 'DIVYA G S'), 
        ('OS-LAB', 'GEENA'), 
        ('DSA-LAB', 'PRIYANKA'),
        ('OOPS-LAB', 'MALA M'),
        ('DV-LAB', 'SHEETHAL')
    ],
    '3C': [
        ('DDCO-LAB', 'SNIGDHA KESH'), 
        ('OS-LAB', 'VEENA BHAT'), 
        ('DSA-LAB', 'PALLAVI KV'),
        ('OOPS-LAB', 'PARTHASARATHY'),
        ('DV-LAB', 'VIJAYALAKSHMI')
    ],
    '3D': [
        ('DDCO-LAB', 'PRAVEEN KUMAR B'), 
        ('OS-LAB', 'RAMYA'), 
        ('DSA-LAB', 'KARTHIGA'),
        ('OOPS-LAB', 'MURALI'),
        ('DV-LAB', 'VEENA BHAT')
    ],
    '3E': [
        ('DDCO-LAB', 'SANGEETHA RAJ'), 
        ('OS-LAB', 'NIRMALA'), 
        ('DSA-LAB', 'BHAVYA'),
        ('OOPS-LAB', 'RADHA'),
        ('DV-LAB', 'ANAND KUMAR B')
    ],
    '3F': [
        ('DDCO-LAB', 'SRINIVAS SETTY'), 
        ('OS-LAB', 'RAMESH'), 
        ('DSA-LAB', 'SANJEEVAN'),
        ('OOPS-LAB', 'PRAVEEN KUMAR'),
        ('DV-LAB', 'RADHA')
    ],

    '5A': [
        ('CN-LAB', 'MAHALAKSHMI B'), 
        ('WEB-LAB', 'ANAND KUMAR B'), 
    ],
    '5B': [
        ('CN-LAB', 'SHEETHAL'), 
        ('WEB-LAB', 'BHAVYA'), 
    ],
    '5C': [
        ('CN-LAB', 'SANGEETHA RAJ'), 
        ('WEB-LAB', 'MURALI'), 
    ],
    '5D': [
        ('CN-LAB', 'YUVARAJ B N, RABHIRDANATH'), 
        ('WEB-LAB', 'GEENA'), 
    ],

    '7A': [
        ('IOT-LAB', 'MAHALAKSHMI B'), 
        ('PC-LAB', 'SHWETHA K R'), 
    ],
    '7B': [
        ('IOT-LAB', 'JAYA KARUNA'), 
        ('PC-LAB', 'VIJAYA NIRMALA'), 
    ],
    '7C': [
        ('IOT-LAB', 'RAMYA'), 
        ('PC-LAB', 'GEENA'), 
    ],
    '7D': [
        ('IOT-LAB', 'SRINIVASA SETTY'), 
        ('PC-LAB', 'SNIGDHA KESH'), 
    ],
}

DAYS = 5
PERIODS = 6