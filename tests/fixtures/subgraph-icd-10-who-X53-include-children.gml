graph [
  directed 1
  node [
    id 0
    label "X53"
    chapter "20"
    block "X50-X57"
    three_char_category "X53"
    description "Lack of food"
    name "X53"
    title ""
    type "code"
    category "category"
    char_len 3
    parent_description "Lack of food"
    formatted_code "X53"
  ]
  node [
    id 1
    label "X50-X57"
    start "X50"
    end "X57"
    chapter_code "20"
    name "X50-X57"
    title "Overexertion, travel and privation"
    type "block"
  ]
  node [
    id 2
    label "root"
  ]
  node [
    id 3
    label "20"
    start "V01"
    end "Y98"
    name "20"
    title "External causes of morbidity and mortality"
    description ""
    type "chapter"
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 2
    target 3
  ]
  edge [
    source 3
    target 1
  ]
]
