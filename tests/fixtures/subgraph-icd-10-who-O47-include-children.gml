graph [
  directed 1
  node [
    id 0
    label "15"
    start "O00"
    end "O99"
    name "15"
    title "Pregnancy, childbirth and the puerperium"
    description ""
    type "chapter"
  ]
  node [
    id 1
    label "root"
  ]
  node [
    id 2
    label "O47"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "False labour"
    name "O47"
    title "False labour"
    type "code"
    category "category"
    char_len 3
    parent_description ""
    formatted_code "O47.-"
  ]
  node [
    id 3
    label "O30-O48"
    start "O30"
    end "O48"
    chapter_code "15"
    name "O30-O48"
    title "Maternal care related to the fetus and amniotic cavity and possible delivery problems"
    type "block"
  ]
  node [
    id 4
    label "O470"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "False labour before 37 completed weeks of gestation"
    name "O470"
    title "False labour"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "False labour before 37 completed weeks of gestation"
    formatted_code "O47.0"
  ]
  node [
    id 5
    label "O471"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "False labour at or after 37 completed weeks of gestation"
    name "O471"
    title "False labour"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "False labour at or after 37 completed weeks of gestation"
    formatted_code "O47.1"
  ]
  node [
    id 6
    label "O479"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "False labour, unspecified"
    name "O479"
    title "False labour"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "False labour, unspecified"
    formatted_code "O47.9"
  ]
  edge [
    source 0
    target 3
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 2
    target 4
  ]
  edge [
    source 2
    target 5
  ]
  edge [
    source 2
    target 6
  ]
  edge [
    source 3
    target 2
  ]
]
