mapData = [
    {
        "key": 1,
        "name": 'Wood',
        "icon": 'https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Wood.png'
    },
    {
        "key": 2,
        "name": 'Metal',
        "icon": 'https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Metal.png'
    },
    {
        "key": 3,
        "name": 'Glass',
        "icon": 'https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Glass.png'
    },
    {
        "key": 4,
        "name": 'Plastic',
        "icon": 'https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Plastic.png'
    },
    {
        "key": 5,
        "name": 'Paper',
        "icon": 'https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Paper.png'
    },
    {
        "key": 6,
        "name": 'Electronic',
        "icon": "https://storage.googleapis.com/greenday-6aba2.appspot.com/Materials/Electronic.png"
    },

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
        "mapData": mapData[1]
    },
    "Picture of an Electronic device": {
        "Material": "Electronic",
        "Recyclability": "Special-Case",
        "mapData": mapData[5]
    },
    "Picture of a Human": {
        "Material": "Human",
        "Recyclability": "Special-Case",
        "mapData": mapData[0]
    },
    "Picture of Rubber or Latex Gloves": {
        "Material": "Rubber",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[0]
    },
    "Picture of Styrofoam": {
        "Material": "Styrofoam",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[3]
    },
    "Picture of Plastic Bag": {
        "Material": "Plastic Bag",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[3]
    },
    "Picture of a Plastic Wrapper or Plastic Film": {
        "Material": "Plastic Wrapper or Film",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[3]
    },
    "Picture of Bubble Wrap": {
        "Material": "Bubble Wrap",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[3]
    },
    "Picture of Shredded Paper": {
        "Material": "Shredded Paper",
        "Recyclability": "Recyclable",
        "mapData": mapData[4]
    },
    "Picture of Soiled Paper": {
        "Material": "Soiled Paper",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[4]
    },
    "Picture of Clean Paper": {
        "Material": "Clean Paper",
        "Recyclability": "Recyclable",
        "mapData": mapData[4]
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
        "mapData": mapData[2]
    },
    "Picture of Cardboard which doesn't contain food": {
        "Material": "Cardboard",
        "Recyclability": "Recyclable",
        "mapData": mapData[0]
    },
    "Picture of a Cardboard which contains pizza": {
        "Material": "Pizza Box",
        "Recyclability": "Not Recyclable",
        "mapData": mapData[0]
    },
    "Picture of an Animal": {
        "Material": "Animal",
        "Recyclability": "Special-Case",
        "mapData": mapData[0]
    },
    "Picture of a Plant": {
        "Material": "Plant",
        "Recyclability": "Bio-degradable",
        "mapData": mapData[0]
    }
}