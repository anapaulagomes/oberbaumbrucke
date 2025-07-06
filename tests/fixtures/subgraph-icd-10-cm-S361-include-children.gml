graph [
  directed 1
  node [
    id 0
    label "19"
    start "S00"
    end "T88"
    name "19"
    title "Injury, poisoning and certain other consequences of external causes (S00-T88)"
    description ""
    type "chapter"
  ]
  node [
    id 1
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
    id 2
    label "S36"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of intra-abdominal organs"
    name "S36"
    title "Injury of intra-abdominal organs"
    type "code"
    category 3
    seventh_char_info ""
  ]
  node [
    id 3
    label "S361"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of liver and gallbladder and bile duct"
    name "S361"
    title "Injury of liver and gallbladder and bile duct"
    type "code"
    category 4
    placeholder 0
  ]
  node [
    id 4
    label "root"
  ]
  node [
    id 5
    label "S3611"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of liver"
    name "S3611"
    title "Injury of liver"
    type "code"
    category 5
    placeholder 0
  ]
  node [
    id 6
    label "S3612"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of gallbladder"
    name "S3612"
    title "Injury of gallbladder"
    type "code"
    category 5
    placeholder 0
  ]
  node [
    id 7
    label "S3613"
    chapter "19"
    block "S30-S39"
    three_char_category "S36"
    description "Injury of bile duct"
    name "S3613"
    title "Injury of bile duct"
    type "code"
    category 5
    placeholder 0
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
    source 2
    target 3
  ]
  edge [
    source 3
    target 5
  ]
  edge [
    source 3
    target 6
  ]
  edge [
    source 3
    target 7
  ]
  edge [
    source 4
    target 0
  ]
]
