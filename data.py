mapData = [
    {
        "key": 0,
        "name": 'Recyclable',
        "icon": 'https://i.imgur.com/CVPZO5u.png'
    },
    {
        "key": 1,
        "name": 'Compostable',
        "icon": 'https://i.imgur.com/rw6KwV3.png'
    },
    {
        "key": 2,
        "name": 'Landfill',
        "icon": 'https://i.imgur.com/D5rAn86.png'
    },
    {
        "key": 3,
        "name": 'E-waste',
        "icon": 'https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Electronic.png'
    },
    {
        "key": 4,
        "name": 'Cardboard',
        "icon": "https://i.imgur.com/AV4ROhB.png"
    },
    {
        "key": 5,
        "name": "Glass",
        "icon": "https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Glass.png"
    }
]

data = {
    "Picture of a Wooden Object": {
        "Material": "Wood",
        "Recyclability": "Recyclable",
        "mapData": mapData[0]
    },
    "Picture of a Metallic Object": {
        "Material": "Metal",
        "Recyclability": "Recyclable",
        "mapData": mapData[0]
    },
    "Picture of an Electronic device": {
        "Material": "Electronic",
        "Recyclability": "Special-Case",
        "mapData": mapData[3]
    },
    "Picture of a Human": {
        "Material": "Human",
        "Recyclability": "Special-Case",
        "mapData": mapData[1]
    },
    "Picture of Rubber or Latex Gloves": {
        "Material": "Rubber",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Styrofoam": {
        "Material": "Styrofoam",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Plastic Bag": {
        "Material": "Plastic Bag",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of a Plastic Wrapper or Plastic Film": {
        "Material": "Plastic Wrapper or Film",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Bubble Wrap": {
        "Material": "Bubble Wrap",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Shredded Paper": {
        "Material": "Shredded Paper",
        "Recyclability": "Recyclable",
        "mapData": mapData[0]
    },
    "Picture of Soiled Paper": {
        "Material": "Soiled Paper",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Clean Paper": {
        "Material": "Clean Paper",
        "Recyclability": "Recyclable",
        "mapData": mapData[0]
    },
    "Picture of Broken Glass": {
        "Material": "Broken Glass",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Ceramic": {
        "Material": "Ceramic",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of Glassware": {
        "Material": "Glassware",
        "Recyclability": "Recyclable",
        "mapData": mapData[5]
    },
    "Picture of Cardboard which doesn't contain food": {
        "Material": "Cardboard",
        "Recyclability": "Recyclable",
        "mapData": mapData[4]
    },
    "Picture of a Cardboard which contains pizza": {
        "Material": "Pizza Box",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[2]
    },
    "Picture of an Animal": {
        "Material": "Animal",
        "Recyclability": "Special-Case",
        "mapData": mapData[1]
    },
    "Picture of a Plant": {
        "Material": "Plant",
        "Recyclability": "Bio-degradable",
        "mapData": mapData[1]
    }
}