graph [
  directed 1
  node [
    id 0
    label "B15-B19"
    start "B15"
    end "B19"
    chapter_code "1"
    name "B15-B19"
    title "Hepatite viral"
    description "None (B15-B19)"
    type "block"
  ]
  node [
    id 1
    label "B18"
  ]
  node [
    id 2
    label "B180"
    chapter "1"
    block "B15-B19"
    three_char_category "B18"
    description "Hepatite viral cr&#244;nica B com agente Delta"
    name "B180"
    title "B18.0 Hepatite viral cronica B c/agente Delta"
    type "code"
  ]
  node [
    id 3
    label "1"
    start "A00"
    end "B99"
    name "1"
    title "I.   Algumas doen&#231;as infecciosas e parasit&#225;rias"
    description "Cap&#237;tulo I - Algumas doen&#231;as infecciosas e parasit&#225;rias"
    type "chapter"
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 1
    target 2
  ]
  edge [
    source 3
    target 0
  ]
]
