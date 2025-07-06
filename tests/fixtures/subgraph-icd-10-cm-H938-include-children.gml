graph [
  directed 1
  node [
    id 0
    label "H93"
    chapter "8"
    block "H90-H94"
    three_char_category "H93"
    description "Other disorders of ear, not elsewhere classified"
    name "H93"
    title "Other disorders of ear, not elsewhere classified"
    type "code"
    category 3
    seventh_char_info ""
  ]
  node [
    id 1
    label "8"
    start "H60"
    end "H95"
    name "8"
    title "Diseases of the ear and mastoid process (H60-H95)"
    description ""
    type "chapter"
  ]
  node [
    id 2
    label "root"
  ]
  node [
    id 3
    label "H90-H94"
    start "H90"
    end "H94"
    chapter_code "8"
    name "H90-H94"
    title "Other disorders of ear"
    description "H90-H94"
    type "block"
  ]
  node [
    id 4
    label "H938"
    chapter "8"
    block "H90-H94"
    three_char_category "H93"
    description "Other specified disorders of ear"
    name "H938"
    title "Other specified disorders of ear"
    type "code"
    category 4
    placeholder 0
  ]
  node [
    id 5
    label "H938X"
    chapter "8"
    block "H90-H94"
    three_char_category "H93"
    description "Other specified disorders of ear"
    name "H938X"
    title "Other specified disorders of ear"
    type "code"
    category 5
    placeholder 1
  ]
  edge [
    source 0
    target 4
  ]
  edge [
    source 1
    target 3
  ]
  edge [
    source 2
    target 1
  ]
  edge [
    source 3
    target 0
  ]
  edge [
    source 4
    target 5
  ]
]
