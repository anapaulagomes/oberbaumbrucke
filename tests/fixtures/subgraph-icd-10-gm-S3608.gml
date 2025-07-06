graph [
  directed 1
  node [
    id 0
    label "S30-S39"
    start "S30"
    end "S39"
    chapter_code "19"
    name "S30-S39"
    title "Verletzungen des Abdomens, der Lumbosakralgegend, der Lendenwirbels&#228;ule und des Beckens"
    description "S30-S39"
    type "block"
  ]
  node [
    id 1
    label "S3608"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Sonstige Verletzungen der Milz"
    name "S3608"
    title "Verletzung von intraabdominalen Organen"
    type "code"
    category 5
    subtitle "Verletzung der Milz"
    formatted_code "S36.08"
  ]
  node [
    id 2
    label "S36"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Verletzung von intraabdominalen Organen"
    name "S36"
    title "Verletzung von intraabdominalen Organen"
    type "code"
    category 3
    subtitle ""
    formatted_code "S36.-"
  ]
  node [
    id 3
    label "19"
    start ""
    end ""
    name "19"
    title "Verletzungen, Vergiftungen und bestimmte andere Folgen &#228;u&#223;erer Ursachen"
    description "Verletzungen, Vergiftungen und bestimmte andere Folgen &#228;u&#223;erer Ursachen"
    type "chapter"
  ]
  node [
    id 4
    label "root"
  ]
  node [
    id 5
    label "S360"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Verletzung der Milz"
    name "S360"
    title "Verletzung von intraabdominalen Organen"
    type "code"
    category 4
    subtitle "Verletzung der Milz"
    formatted_code "S36.0-"
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 2
    target 5
  ]
  edge [
    source 3
    target 0
  ]
  edge [
    source 4
    target 3
  ]
  edge [
    source 5
    target 1
  ]
]
