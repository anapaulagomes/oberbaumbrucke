graph [
  directed 1
  node [
    id 0
    label "B18"
    chapter 1
    block "B15-B19"
    three_char_category "B18"
    description ""
    name "B18"
    title "Hepatite viral cronica"
    type "code"
    category "category"
    char_len 3
  ]
  node [
    id 1
    label "B180"
    chapter 1
    block "B15-B19"
    three_char_category "B18"
    description ""
    name "B180"
    title "Hepatite viral cronica B com agente Delta"
    type "code"
    category "subcategory"
    char_len 4
  ]
  node [
    id 2
    label "B15-B19"
    start "B15"
    end "B19"
    chapter_code "1"
    name "B15-B19"
    title "Hepatite viral"
    type "block"
  ]
  node [
    id 3
    label "root"
  ]
  node [
    id 4
    label "1"
    start "A00"
    end "B99"
    name "1"
    title "Algumas doen&#231;as infecciosas e parasit&#225;rias"
    description ""
    type "chapter"
  ]
  edge [
    source 0
    target 1
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
    target 2
  ]
]
