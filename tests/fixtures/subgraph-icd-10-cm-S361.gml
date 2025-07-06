graph [
  directed 1
  node [
    id 0
    label "S361"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of liver and gallbladder and bile duct"
    name "S361"
    title ""
    type "code"
    category 4
    placeholder 0
  ]
  node [
    id 1
    label "root"
  ]
  node [
    id 2
    label "S30-S39"
    start "S30"
    end "S39"
    chapter_code "19"
    name "S30-S39"
    title "Injuries to the abdomen, lower back, lumbar spine, pelvis and external genitals"
    description "S30-S39"
    type "block"
  ]
  node [
    id 3
    label "S36"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of intra-abdominal organs"
    name "S36"
    title ""
    type "code"
    category 3
    seventh_char_info ""
  ]
  node [
    id 4
    label "19"
    start "S00"
    end "T88"
    name "19"
    title "Injury, poisoning and certain other consequences of external causes (S00-T88)"
    description ""
    type "chapter"
  ]
  edge [
    source 1
    target 4
  ]
  edge [
    source 2
    target 3
  ]
  edge [
    source 3
    target 0
  ]
  edge [
    source 4
    target 2
  ]
]
