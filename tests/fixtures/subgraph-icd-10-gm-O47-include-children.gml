graph [
  directed 1
  node [
    id 0
    label "O47"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "Frustrane Kontraktionen [Unn&#252;tze Wehen]"
    name "O47"
    title "Frustrane Kontraktionen [Unn&#252;tze Wehen]"
    type "code"
    category "category"
    char_len 3
    parent_description ""
    formatted_code "O47.-"
  ]
  node [
    id 1
    label "15"
    start "O00"
    end "O99"
    name "15"
    title "Schwangerschaft, Geburt und Wochenbett"
    description ""
    type "chapter"
  ]
  node [
    id 2
    label "O30-O48"
    start "O30"
    end "O48"
    chapter_code "15"
    name "O30-O48"
    title "Betreuung der Mutter im Hinblick auf den Fetus und die Amnionh&#246;hle sowie m&#246;gliche Entbindungskomplikationen"
    type "block"
  ]
  node [
    id 3
    label "root"
  ]
  node [
    id 4
    label "O470"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "Frustrane Kontraktionen vor 37 vollendeten Schwangerschaftswochen"
    name "O470"
    title "Frustrane Kontraktionen [Unn&#252;tze Wehen]"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "Frustrane Kontraktionen vor 37 vollendeten Schwangerschaftswochen"
    formatted_code "O47.0"
  ]
  node [
    id 5
    label "O471"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "Frustrane Kontraktionen ab 37 oder mehr vollendeten Schwangerschaftswochen"
    name "O471"
    title "Frustrane Kontraktionen [Unn&#252;tze Wehen]"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "Frustrane Kontraktionen ab 37 oder mehr vollendeten Schwangerschaftswochen"
    formatted_code "O47.1"
  ]
  node [
    id 6
    label "O479"
    chapter "15"
    block "O30-O48"
    three_char_category "O47"
    description "Frustrane Kontraktionen, nicht n&#228;her bezeichnet"
    name "O479"
    title "Frustrane Kontraktionen [Unn&#252;tze Wehen]"
    type "code"
    category "subcategory"
    char_len 4
    parent_description "Frustrane Kontraktionen, nicht n&#228;her bezeichnet"
    formatted_code "O47.9"
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
    source 1
    target 2
  ]
  edge [
    source 2
    target 0
  ]
  edge [
    source 3
    target 1
  ]
]
