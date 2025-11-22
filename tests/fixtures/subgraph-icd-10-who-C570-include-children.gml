graph [
  directed 1
  node [
    id 0
    label "C51-C58"
    start "C51"
    end "C58"
    chapter_code "2"
    name "C51-C58"
    title "Malignant neoplasms of female genital organs"
    type "block"
  ]
  node [
    id 1
    label "root"
  ]
  node [
    id 2
    label "C57"
    chapter "02"
    block "C51-C58"
    three_char_category "C57"
    description "Malignant neoplasm of other and unspecified female genital organs"
    name "C57"
    title "Malignant neoplasm of other and unspecified female genital organs"
    type "code"
    category "category"
    char_len 3
    parent_description ""
    formatted_code "C57.-"
  ]
  node [
    id 3
    label "2"
    start "C00"
    end "D48"
    name "2"
    title "Neoplasms"
    description ""
    type "chapter"
  ]
  node [
    id 4
    label "C570"
    chapter "02"
    block "C51-C58"
    three_char_category "C57"
    description "Malignant neoplasm: Fallopian tube"
    name "C570"
    title "Malignant neoplasm of other and unspecified female genital organs"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "Fallopian tube"
    formatted_code "C57.0"
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 1
    target 3
  ]
  edge [
    source 2
    target 4
  ]
  edge [
    source 3
    target 0
  ]
]
