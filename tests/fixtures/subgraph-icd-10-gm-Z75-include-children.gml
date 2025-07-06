graph [
  directed 1
  node [
    id 0
    label "Z75"
    chapter "21"
    block "Z70-Z76"
    three_char_category "Z75"
    description "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    name "Z75"
    title "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    type "code"
    category 3
    subtitle ""
    formatted_code "Z75.-"
  ]
  node [
    id 1
    label "Z70-Z76"
    start "Z70"
    end "Z76"
    chapter_code "21"
    name "Z70-Z76"
    title "Personen, die das Gesundheitswesen aus sonstigen Gr&#252;nden in Anspruch nehmen"
    description "Z70-Z76"
    type "block"
  ]
  node [
    id 2
    label "21"
    start "Z00"
    end "Z99"
    name "21"
    title "Faktoren, die den Gesundheitszustand beeinflussen und zur Inanspruchnahme des Gesundheitswesens f&#252;hren"
    description "Faktoren, die den Gesundheitszustand beeinflussen und zur Inanspruchnahme des Gesundheitswesens f&#252;hren"
    type "chapter"
  ]
  node [
    id 3
    label "root"
  ]
  node [
    id 4
    label "Z752"
    chapter "21"
    block "Z70-Z76"
    three_char_category "Z75"
    description "Wartezeit auf eine Untersuchung oder Behandlung"
    name "Z752"
    title "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    type "code"
    category 4
    subtitle "Wartezeit auf eine Untersuchung oder Behandlung"
    formatted_code "Z75.2"
  ]
  node [
    id 5
    label "Z756"
    chapter "21"
    block "Z70-Z76"
    three_char_category "Z75"
    description "Erfolgte Registrierung zur Organtransplantation ohne Dringlichkeitsstufe HU (High Urgency)"
    name "Z756"
    title "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    type "code"
    category 4
    subtitle "Erfolgte Registrierung zur Organtransplantation ohne Dringlichkeitsstufe HU (High Urgency)"
    formatted_code "Z75.6-"
  ]
  node [
    id 6
    label "Z757"
    chapter "21"
    block "Z70-Z76"
    three_char_category "Z75"
    description "Erfolgte Registrierung zur Organtransplantation mit Dringlichkeitsstufe HU (High Urgency)"
    name "Z757"
    title "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    type "code"
    category 4
    subtitle "Erfolgte Registrierung zur Organtransplantation mit Dringlichkeitsstufe HU (High Urgency)"
    formatted_code "Z75.7-"
  ]
  node [
    id 7
    label "Z758"
    chapter "21"
    block "Z70-Z76"
    three_char_category "Z75"
    description "Sonstige Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    name "Z758"
    title "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    type "code"
    category 4
    subtitle "Sonstige Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    formatted_code "Z75.8"
  ]
  node [
    id 8
    label "Z759"
    chapter "21"
    block "Z70-Z76"
    three_char_category "Z75"
    description "Nicht n&#228;her bezeichnetes Problem mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    name "Z759"
    title "Probleme mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    type "code"
    category 4
    subtitle "Nicht n&#228;her bezeichnetes Problem mit Bezug auf medizinische Betreuungsm&#246;glichkeiten oder andere Gesundheitsversorgung"
    formatted_code "Z75.9"
  ]
  edge [
    source 0
    target 4
  ]
  edge [
    source 0
    target 5
  ]
  edge [
    source 0
    target 6
  ]
  edge [
    source 0
    target 7
  ]
  edge [
    source 0
    target 8
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 2
    target 1
  ]
  edge [
    source 3
    target 2
  ]
]
