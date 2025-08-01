const gameData = {
  game_state: {
    current_player_name: "Player A",
    players: [
      {
        name: "Player A",
        banked_cards: [
          {name: "$2M", value: 2, type: "MONEY"},
          {name: "$3M", value: 3, type: "MONEY"}
        ],
        property_sets: {
          RED: {
            set_color: "RED",
            cards: [
              {name:"Kentucky Ave", value: 3, type:"PROPERTY", set_color:"RED"},
              {name:"Indiana Ave", value: 3, type:"PROPERTY", set_color:"RED"}
            ],
            number_for_full_set: 3,
            is_full_set: false
          },
          GREEN: {
            set_color:"GREEN",
            cards:[
              {name:"Pacific Ave", value:4, type:"PROPERTY", set_color:"GREEN"},
              {name:"North Carolina Ave", value:4, type:"PROPERTY", set_color:"GREEN"},
              {name:"Pennsylvania Ave", value:4, type:"PROPERTY", set_color:"GREEN"}
            ],
            number_for_full_set: 3,
            is_full_set: true
          }
        },
        hand_cards:[
          {name:"just say no", type:"ACTION_JUST_SAY_NO", value:4},
          {name:"sunset blvd", type:"PROPERTY", set_color:"ORANGE", value:2},
          {name:"$2M", type:"MONEY", value:2}
        ]
      },
      {
        name:"Player B",
        banked_cards:[{name:"$1M", value:1, type:"MONEY"}],
        property_sets:{},
        hand_cards:[
          {name:"deal breaker", type:"ACTION", value:5},
          {name:"$3M", type:"MONEY", value:3}
        ]
      }
    ]
  },
  winner: "Player A"
};
