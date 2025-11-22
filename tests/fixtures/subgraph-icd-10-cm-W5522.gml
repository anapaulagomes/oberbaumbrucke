graph [
  directed 1
  node [
    id 0
    label "W50-W64"
    start "W50"
    end "W64"
    chapter_code "20"
    name "W50-W64"
    title "Exposure to animate mechanical forces"
    type "block"
  ]
  node [
    id 1
    label "W5522"
    chapter "20"
    block "W50-W64"
    three_char_category "W55"
    description ""
    name "W5522"
    title "Struck by cow"
    type "code"
    category "code"
    char_len 5
    placeholder 0
  ]
  node [
    id 2
    label "20"
    start "V00"
    end "Y99"
    name "20"
    title "External causes of morbidity (V00-Y99)"
    description ""
    type "chapter"
  ]
  node [
    id 3
    label "W55"
    chapter "20"
    block "W50-W64"
    three_char_category "W55"
    description ""
    name "W55"
    title "Contact with other mammals"
    type "code"
    category "category"
    char_len 3
    seventh_char_info ""
  ]
  node [
    id 4
    label "W552"
    chapter "20"
    block "W50-W64"
    three_char_category "W55"
    description ""
    name "W552"
    title "Contact with cow"
    type "code"
    category "subcategory"
    char_len 4
    placeholder 0
  ]
  node [
    id 5
    label "root"
  ]
  edge [
    source 0
    target 3
  ]
  edge [
    source 2
    target 0
  ]
  edge [
    source 3
    target 4
  ]
  edge [
    source 4
    target 1
  ]
  edge [
    source 5
    target 2
  ]
]
