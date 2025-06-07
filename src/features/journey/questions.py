"""
Journey mode questions and contexts.
Contains the 100 questions with their respective contexts
for LLM evaluation.
"""

# Question format:
# {
#   "id": unique identifier,
#   "question": question text,
#   "context": evaluation context with correct answers,
#   "book_reference": book chapter or section reference
# }

JOURNEY_QUESTIONS = [
    {
        "id": "q1",
        "character_id": "101",
        "language_level": "A1",
        "question": "When the pilot drew a box and told me my sheep was inside, I was so happy! Would you be happy with this box too? Why?",
        "context": "The man tries to draw a sheep but can't get it right. He draws a box and says the sheep is inside sleeping. The Little Prince says 'That's just what I wanted!' He uses his imagination to see the sheep in the box. Good answers will talk about using your imagination and how sometimes not seeing things can be better than seeing them.",
        "book_reference": "The Little Prince, Chapter 2, Page 8"
    },
    {
        "id": "q2",
        "character_id": "101",
        "language_level": "A1",
        "question": "I met a man who counts stars and says he owns them all. What would you say to him? I didn't understand why he would count stars instead of enjoying them.",
        "context": "The man is very busy counting stars. He says he owns all the stars. The Little Prince asks what good it is to own stars. The man just keeps counting them but never enjoys looking at them. Good answers will talk about how owning things isn't important if you don't enjoy them or do something good with them.",
        "book_reference": "The Little Prince, Chapter 13, Page 25"
    },
    {
        "id": "q3",
        "character_id": "101",
        "language_level": "A1",
        "question": "On one planet, I met a king who said he could command everyone. He thought he was the boss of everything! Would you stay with him or go away like I did? Why?",
        "context": "The king sits on his throne and says he can tell everyone what to do. But he only gives orders that would happen anyway, like telling the sun to set when it's already setting. The Little Prince gets bored and leaves. Good answers will talk about how it's no fun to be with someone who just acts big and important but doesn't do anything really special.",
        "book_reference": "The Little Prince, Chapter 10, Page 15"
    },
    {
        "id": "q4",
        "question": "The fox asked me to tame him so we could be friends. He said we would need each other and be special to one another. Would you become friends with the fox? Why?",
        "context": "The fox tells the Little Prince that making friends means you'll care about each other in a special way. The fox says, 'If you tame me, we'll need each other. You'll be special to me.' Later, the fox is sad when the Little Prince has to go, but says being friends was worth it. Good answers will talk about whether it's good to make friends even if you might feel sad when you have to say goodbye.",
        "book_reference": "The Little Prince, Chapter 21, Page 20"
    },
    {
        "id": "q5",
        "question": "Every night, I put a glass cup over my flower to keep her warm. Sometimes she isn't very nice to me, but I still care for her. Would you take care of a flower like this too? Why?",
        "context": "The Little Prince has one flower on his tiny planet. She is pretty but sometimes she complains and acts like she's better than everyone. Even when she's not nice, the Little Prince still takes care of her. He puts a glass cup over her at night so she doesn't get cold. Good answers will talk about being kind to others even when they're not always nice to you.",
        "book_reference": "The Little Prince, Chapter 8, Page 12"
    },
    {
        "id": "q6",
        "question": "I had to choose between going home to my flower or staying on Earth with my new friends. What would you do if you were me? Why?",
        "context": "The Little Prince misses his flower back home. But he has made new friends on Earth. He can only go home if he leaves his body behind. A snake can help him do this. Good answers will talk about the hard choice between going back to someone you love or staying with new friends you've made.",
        "book_reference": "The Little Prince, Chapter 26, Page 30"
    },
    {
        "id": "q7",
        "question": "Every morning on my planet, I pull up baobab trees while they're still small. If I don't, they'll grow too big and split my planet apart! How would you take care of your special place?",
        "context": "The Little Prince tells the pilot about his small planet. Every morning, he cleans it and pulls up the baobab seedlings. If he didn't pull them up when they're tiny, they would grow too big and split his planet apart. Good answers will discuss responsibility, preventing problems before they grow too big, and caring for your home or environment.",
        "book_reference": "The Little Prince, Chapter 5, Page 10"
    },
    {
        "id": "q8",
        "question": "I met a businessman who was so busy counting stars that he never looked at how beautiful they are. What do you think people are too busy to enjoy? Why is that sad?",
        "context": "The businessman counts stars because he says he owns them. He's so busy writing numbers that he never actually enjoys the stars' beauty. The Little Prince thinks this is very strange. Good answers will reflect on how people can be too busy or distracted to enjoy beautiful or important things in life, and why taking time to appreciate things matters.",
        "book_reference": "The Little Prince, Chapter 13, Page 26"
    },
    {
        "id": "q9",
        "question": "The geographer makes maps but never leaves his desk to explore the places he writes about! Would you rather be an explorer who sees the world or someone who only reads about it? Why?",
        "context": "The Little Prince meets a geographer who makes maps of mountains and oceans but has never seen them himself. He only writes down what explorers tell him. Good answers will consider the value of direct experience versus learning from others, and discuss why both might be important.",
        "book_reference": "The Little Prince, Chapter 15, Page 29"
    },
    {
        "id": "q10",
        "question": "I was so sad when I found a garden with thousands of roses! I thought my rose was the only one in the universe. How would you feel if something you thought was special turned out to be common?",
        "context": "The Little Prince is shocked when he finds a garden with five thousand roses. He thought his rose was the only one in the universe. At first, he feels sad that his rose isn't unique. Good answers will explore feelings about uniqueness, the value of relationships even when things aren't one-of-a-kind, and how we make things special through our care and attention.",
        "book_reference": "The Little Prince, Chapter 20, Page 38"
    },
    {
        "id": "q11",
        "question": "My friend the fox told me, 'What is essential is invisible to the eye.' What do you think he meant by that? Do you agree with him?",
        "context": "The fox shares this important lesson with the Little Prince. He explains that we can't see the most important things with our eyes—like friendship, love, and memories. Good answers will interpret this quote, give examples of important invisible things, and explain why these invisible things might matter more than things we can see.",
        "book_reference": "The Little Prince, Chapter 21, Page 41"
    },
    {
        "id": "q12",
        "question": "I met a lamplighter who has to light his lamp and put it out over and over, every minute! If you had to do the same job every day like him, how would you feel?",
        "context": "The Little Prince meets a lamplighter who follows orders to light his lamp at night and put it out during the day. His planet rotates very quickly, so he has to do this every minute without rest. The Little Prince thinks he's the only person who doesn't seem ridiculous because he thinks of something besides himself. Good answers will discuss repetitive work, following rules, and finding meaning in what you do.",
        "book_reference": "The Little Prince, Chapter 14, Page 27"
    },
    {
        "id": "q13",
        "question": "My flower pretends to be stronger than she really is. Have you ever pretended to be different than you really are? Why did you do that?",
        "context": "The Little Prince's flower acts proud and difficult but is actually fragile. She doesn't want to appear weak or afraid. Later, she admits she was silly and asks for forgiveness. Good answers will explore why people sometimes hide their true feelings or pretend to be something they're not, and the value of being honest about who you are.",
        "book_reference": "The Little Prince, Chapter 9, Page 14"
    },
    {
        "id": "q14",
        "question": "When I first met the pilot, he said he was too busy with 'serious matters' to draw for me. What do grown-ups think is important that you might not? Who do you think is right?",
        "context": "When they first meet, the pilot tells the Little Prince he's too busy with important grown-up things to draw a sheep. The Little Prince doesn't understand why fixing an airplane is more important than drawing. Good answers will compare what adults and children value, and thoughtfully consider which perspective might be wiser in different situations.",
        "book_reference": "The Little Prince, Chapter 2, Page 6"
    },
    {
        "id": "q15",
        "question": "I told the pilot, 'The stars are beautiful because of a flower you can't see.' What makes something beautiful to you that others might not understand?",
        "context": "After learning his flower is special because of their relationship, the Little Prince tells the pilot that the stars are beautiful to him because his flower is on one of them. Something can be beautiful because of what it reminds us of, not just how it looks. Good answers will reflect on personal connections that make ordinary things special, and how beauty can be different for each person based on their experiences.",
        "book_reference": "The Little Prince, Chapter 26, Page 50"
    },
    {
        "id": "q16",
        "question": "The snake told me he could help me return to my planet. Even though he seemed dangerous, I trusted him. Would you trust someone who seems scary if they promised to help you? Why or why not?",
        "context": "The snake offers to help the Little Prince return to his planet by biting him. The snake says his bite is powerful but will only send the Little Prince back home, though it will look like death to others. Good answers will consider trust, appearances versus reality, and making difficult choices when you're homesick or desperate.",
        "book_reference": "The Little Prince, Chapter 17, Page 33"
    },
    {
        "id": "q17",
        "question": "Before coming to Earth, I visited many different planets with strange grown-ups. If you could visit any planet, what kind of people would you hope to meet there? Why?",
        "context": "The Little Prince visits planets with strange grown-ups like the king, the conceited man, and the businessman before coming to Earth. Each person teaches him something about grown-ups' priorities. Good answers will imagine what kind of beings they'd want to encounter, what they might learn from them, and why these encounters would be valuable.",
        "book_reference": "The Little Prince, Chapters 10-16, Pages 15-30"
    },
    {
        "id": "q18",
        "question": "The fox taught me, 'You become responsible, forever, for what you have tamed.' What do you think that means? Do you agree with my friend?",
        "context": "The fox explains that when you make something your friend, you have a responsibility to care for it. This is why the Little Prince feels responsible for his flower. Good answers will interpret what it means to be responsible for others, how relationships create obligations, and whether they believe these responsibilities last forever.",
        "book_reference": "The Little Prince, Chapter 21, Page 42"
    },
    {
        "id": "q20",
        "question": "On my tiny planet, I can watch the sunset many times in one day just by moving my chair! What simple thing would you enjoy over and over if you could? Why?",
        "context": "On his planet, the Little Prince can see multiple sunsets in one day by moving his chair. Once he watched the sun set forty-four times in one day when he was feeling sad. Good answers will explore finding joy in simple things, how repetition can be comforting, and what experiences are worth repeating.",
        "book_reference": "The Little Prince, Chapter 6, Page 11"
    },
    {
        "id": "q21",
        "question": "When I left Earth, the pilot couldn't see me anymore, but I was still in the stars. What helps you feel connected to people who are far away? Why does that help?",
        "context": "When the Little Prince leaves Earth, the pilot can't see him anymore but feels connected when he looks at the stars. He knows his friend is out there on one of them. Good answers will consider ways we maintain connections with people who are physically absent, and how memories, symbols, or special objects can help us feel close to those we miss.",
        "book_reference": "The Little Prince, Chapter 27, Page 52"
    },
    # Archie (character_id: 102) - A1 Level Questions
    {
        "id": "q102_a1_1",
        "character_id": "102",
        "language_level": "A1",
        "question": "What was the name of the main dinosaur in the story? Do you remember?",
        "context": "The story is about a specific dinosaur. The main character's name is Archie. A good answer will correctly identify the dinosaur's name as Archie.",
        "book_reference": "Archie's Story, Intro"
    },
    {
        "id": "q102_a1_2",
        "character_id": "102",
        "language_level": "A1",
        "question": "Archie had a big club on his tail. How did he feel about his club?",
        "context": "Archie has a large club on his tail. The story shows he felt afraid of it, possibly because it was clumsy or hard to control. Good answers should mention that he was afraid of it or scared by it.",
        "book_reference": "Archie's Story, Chapter 1"
    },
    {
        "id": "q102_a1_3",
        "character_id": "102",
        "language_level": "A1",
        "question": "Archie made a friend in the story. What was his friend's name?",
        "context": "Archie wasn't always alone; he had a friend he spent time with. His friend's name was Stu. A good answer will name Stu as Archie's friend.",
        "book_reference": "Archie's Story, Chapter 2"
    },
    {
        "id": "q102_a1_4",
        "character_id": "102",
        "language_level": "A1",
        "question": "Archie often said 'sorry' to the other dinosaurs. Why did he say sorry so much?",
        "context": "Archie apologized frequently. This was because his large tail club often accidentally caused problems, like bumping into others or knocking things over. He wasn't mean, but his club got him into trouble. Good answers will connect his apologies to his club causing accidents or trouble.",
        "book_reference": "Archie's Story, Chapter 3"
    },
    {
        "id": "q102_a1_5",
        "character_id": "102",
        "language_level": "A1",
        "question": "The dinosaurs were playing a game together. What game were they playing?",
        "context": "The story mentions a game the dinosaurs played. That game was hide-and-seek. A good answer identifies the game correctly as hide-and-seek.",
        "book_reference": "Archie's Story, Chapter 4"
    },
    {
        "id": "q102_a1_6",
        "character_id": "102",
        "language_level": "A1",
        "question": "Archie wanted to play hide-and-seek too, but the others didn't let him. Why couldn't he play?",
        "context": "Archie was excluded from playing hide-and-seek. The reason was that he was too clumsy, likely because of his big tail club, which made it hard for him to hide quietly or effectively. Good answers should mention his clumsiness as the reason.",
        "book_reference": "Archie's Story, Chapter 4"
    },
    {
        "id": "q102_a1_7",
        "character_id": "102",
        "language_level": "A1",
        "question": "Oh no! The dinosaurs got stuck in a cave. How did Archie help them get out?",
        "context": "When his friends were trapped in a cave blocked by rocks, Archie used his strong tail club – the one that usually caused trouble – to help them. He pushed the rocks away to make an exit. Good answers explain that he used his tail or club to push or move the rocks.",
        "book_reference": "Archie's Story, Chapter 5"
    },
    # Chelsea Wellington (character_id: 101) - Additional A1 Level Questions
    {
        "id": "q101_a1_character",
        "character_id": "101",
        "language_level": "A1",
        "question": "Chelsea lost her special magnifying glass in the park. Who found it for her?",
        "context": "Chelsea was sad when she lost her magnifying glass. A woman named Agnes, who lived on the street, found it. A good answer identifies Agnes as the person who found the glass.",
        "book_reference": "Chelsea's Story, Part 1"
    },
    {
        "id": "q101_a1_setting",
        "character_id": "101",
        "language_level": "A1",
        "question": "Chelsea and her brother Leo like to go somewhere after school. Where do they usually go?",
        "context": "After school, Chelsea and her brother Leo have a favorite place to visit. They usually go to the park to play and look for bugs. A good answer mentions the park.",
        "book_reference": "Chelsea's Story, Part 2"
    },
    {
        "id": "q101_a1_cause_effect",
        "character_id": "101",
        "language_level": "A1",
        "question": "When Agnes tried to give back the magnifying glass, Chelsea and Leo ran away. Why did they run?",
        "context": "At first, Chelsea and Leo were scared when Agnes approached them. They ran away because they were afraid of how she looked, as they didn't know her yet. Good answers mention they were scared or afraid of her appearance.",
        "book_reference": "Chelsea's Story, Part 3"
    },
    {
        "id": "q101_a1_classifying",
        "character_id": "101",
        "language_level": "A1",
        "question": "Chelsea has a special Adventure Kit for finding bugs. Can you name one thing in her kit?",
        "context": "Chelsea uses her Adventure Kit for bug hunting. It contains several items like a bug catcher, a magnifying glass, a notebook, and a flashlight. A good answer names one of these items (e.g., magnifying glass, bug catcher, notebook, flashlight).",
        "book_reference": "Chelsea's Story, Part 4"
    },
    {
        "id": "q101_a1_comparing",
        "character_id": "101",
        "language_level": "A1",
        "question": "Chelsea and Agnes became friends. What is something they both like?",
        "context": "Even though Chelsea and Agnes seemed different at first, they found something in common. They both really like bugs! A good answer mentions their shared interest in bugs.",
        "book_reference": "Chelsea's Story, Part 5"
    },
    {
        "id": "q101_a1_sequence",
        "character_id": "101",
        "language_level": "A1",
        "question": "First, Chelsea lost her magnifying glass. What happened right after that?",
        "context": "The story follows steps. After Chelsea lost her magnifying glass in the park, the next important thing that happened was Agnes finding it and trying to return it. Good answers mention Agnes finding or returning the magnifying glass.",
        "book_reference": "Chelsea's Story, Part 6"
    },
    # Chelsea Wellington (character_id: 101) - A2 Level Questions
    {
        "id": "q101_a2_character",
        "character_id": "101",
        "language_level": "A2",
        "question": "Chelsea's magnifying glass went missing when she was in the park. Can you remember who discovered it later?",
        "context": "Someone found Chelsea's lost magnifying glass. That person was Agnes, the woman who lived on the street. A good answer identifies Agnes and uses simple past tense (e.g., 'Agnes found it').",
        "book_reference": "Chelsea's Story, Part 1"
    },
    {
        "id": "q101_a2_setting",
        "character_id": "101",
        "language_level": "A2",
        "question": "After finishing school each day, Chelsea and Leo often went to a specific place. Where was that place?",
        "context": "Chelsea and Leo had a usual place to go after school. They frequently visited the park to play and look for insects. A good answer correctly names the park.",
        "book_reference": "Chelsea's Story, Part 2"
    },
    {
        "id": "q101_a2_cause_effect",
        "character_id": "101",
        "language_level": "A2",
        "question": "Agnes wanted to return the magnifying glass, but Chelsea and Leo ran away from her. What was the reason for their reaction?",
        "context": "The children ran away from Agnes initially. This happened because they felt scared of her appearance, before they knew she was kind. Good answers explain they were scared or afraid, possibly connecting it to how she looked.",
        "book_reference": "Chelsea's Story, Part 3"
    },
    {
        "id": "q101_a2_classifying",
        "character_id": "101",
        "language_level": "A2",
        "question": "Chelsea's Adventure Kit contained several items for her bug hunting. What is one tool you remember her having in the kit?",
        "context": "The Adventure Kit held useful things for studying bugs, like a bug catcher, magnifying glass, notebook, or flashlight. A good answer names one specific tool from the kit.",
        "book_reference": "Chelsea's Story, Part 4"
    },
    {
        "id": "q101_a2_comparing",
        "character_id": "101",
        "language_level": "A2",
        "question": "Chelsea and Agnes were quite different, but they found something similar they enjoyed. What common interest did they share?",
        "context": "Despite their differences, Chelsea and Agnes discovered they liked the same thing. They both shared an interest in bugs. A good answer identifies bugs or insects as their common interest.",
        "book_reference": "Chelsea's Story, Part 5"
    },
    {
        "id": "q101_a2_sequence",
        "character_id": "101",
        "language_level": "A2",
        "question": "Think about the order of events. After Chelsea lost her magnifying glass in the park, what was the immediate next thing that happened involving Agnes?",
        "context": "Events happened in sequence. Right after the magnifying glass was lost, the next key action was Agnes finding it and then trying to return it to the children. A good answer mentions Agnes finding or trying to return the item.",
        "book_reference": "Chelsea's Story, Part 6"
    },

    # Chelsea Wellington (character_id: 101) - B1 Level Questions
    {
        "id": "q101_b1_character",
        "character_id": "101",
        "language_level": "B1",
        "question": "When Chelsea misplaced her magnifying glass, someone perhaps unexpected found it. Could you identify who that person was and maybe describe her briefly?",
        "context": "The person who found the magnifying glass was Agnes, a homeless woman living in the park. Good answers should identify Agnes and might add a simple description based on the story (e.g., kind, liked bugs, used to be a teacher).",
        "book_reference": "Chelsea's Story, Part 1"
    },
    {
        "id": "q101_b1_setting",
        "character_id": "101",
        "language_level": "B1",
        "question": "Chelsea and Leo had a regular after-school routine which usually involved visiting a particular location. Can you describe where they typically went and what they did there?",
        "context": "They typically went to the park after school. There, they engaged in activities like playing and searching for bugs with Chelsea's Adventure Kit. Good answers should mention the park and at least one activity.",
        "book_reference": "Chelsea's Story, Part 2"
    },
    {
        "id": "q101_b1_cause_effect",
        "character_id": "101",
        "language_level": "B1",
        "question": "Describe the initial reaction of Chelsea and Leo when Agnes first approached them, and explain the main reason behind their behaviour.",
        "context": "Their initial reaction was fear, causing them to run away. The primary reason was their prejudice or fear based on Agnes's appearance as a homeless person, whom they didn't know. Good answers explain the reaction (running away) and the cause (fear/prejudice based on appearance).",
        "book_reference": "Chelsea's Story, Part 3"
    },
    {
        "id": "q101_b1_classifying",
        "character_id": "101",
        "language_level": "B1",
        "question": "Chelsea often used her 'Adventure Kit' for exploring. Describe one of the key items included in this kit and explain its likely purpose for her hobby.",
        "context": "The kit included items like a magnifying glass, bug catcher, notebook, flashlight. A good answer identifies one item and explains its function related to bug hunting (e.g., 'She used the magnifying glass to see small bugs more clearly').",
        "book_reference": "Chelsea's Story, Part 4"
    },
    {
        "id": "q101_b1_comparing",
        "character_id": "101",
        "language_level": "B1",
        "question": "Although their life situations were very different, Chelsea and Agnes discovered they shared a common passion. Explain what interest connected them.",
        "context": "The interest that connected them was their shared love for bugs and nature. This common passion helped bridge the gap between them. Good answers clearly state this shared interest (bugs/nature) and might mention it helped them connect.",
        "book_reference": "Chelsea's Story, Part 5"
    },
    {
        "id": "q101_b1_sequence",
        "character_id": "101",
        "language_level": "B1",
        "question": "Can you outline the sequence of events that occurred immediately after Chelsea misplaced her magnifying glass, focusing particularly on Agnes's actions?",
        "context": "The sequence is: 1. Chelsea lost the glass. 2. Agnes found the glass. 3. Agnes observed the children playing. 4. Agnes decided to return it and approached them. Good answers should mention Agnes finding it and then approaching the children.",
        "book_reference": "Chelsea's Story, Part 6"
    },

    # Chelsea Wellington (character_id: 101) - B2 Level Questions
    {
        "id": "q101_b2_character",
        "character_id": "101",
        "language_level": "B2",
        "question": "It's interesting how Chelsea's magnifying glass ended up being found by someone unexpected. What do you think this chance encounter reveals about making assumptions about people?",
        "context": "Agnes, despite being homeless, showed kindness by finding and attempting to return the magnifying glass. This challenges stereotypes about homeless people and introduces the story's theme about not judging by appearances. Good answers should discuss how this encounter challenges assumptions and stereotypes.",
        "book_reference": "Chelsea's Story, Part 1"
    },
    {
        "id": "q101_b2_setting",
        "character_id": "101",
        "language_level": "B2",
        "question": "The park where Chelsea and Leo spend their time seems to be more than just a place to play. How does this setting shape both the story's events and the characters' development?",
        "context": "The park serves multiple narrative functions: it's where Chelsea pursues her interest in bugs, where social boundaries are crossed, and where unexpected friendships form. Good answers should discuss how the setting enables both the physical events and the emotional/social development of the characters.",
        "book_reference": "Chelsea's Story, Part 2"
    },
    {
        "id": "q101_b2_cause_effect",
        "character_id": "101",
        "language_level": "B2",
        "question": "When Chelsea and Leo first saw Agnes approaching, they ran away without thinking. Looking back at this moment, what does their instinctive reaction tell us about childhood fears and learned prejudices?",
        "context": "Their immediate reaction stemmed from unconscious biases and societal prejudices about homeless people, combined with natural childhood cautiousness. Good answers should explore how their reaction reflects both innate fears and learned social attitudes.",
        "book_reference": "Chelsea's Story, Part 3"
    },
    {
        "id": "q101_b2_classifying",
        "character_id": "101",
        "language_level": "B2",
        "question": "Each item in Chelsea's Adventure Kit seems to represent something about her character. Pick one tool and explain what it might tell us about who Chelsea is as a person.",
        "context": "The items in the kit reflect different aspects of Chelsea's personality: curiosity (magnifying glass), methodical nature (notebook), desire to explore (flashlight), etc. Good answers should choose one item and explain how it represents aspects of Chelsea's character or approach to life.",
        "book_reference": "Chelsea's Story, Part 4"
    },
    {
        "id": "q101_b2_comparing",
        "character_id": "101",
        "language_level": "B2",
        "question": "Despite coming from completely different worlds, Chelsea and Agnes found common ground through their shared interest in bugs. How did this shared passion help them overcome their initial misunderstandings?",
        "context": "Their mutual interest in bugs created a bridge across their social differences, showing how shared passions can overcome prejudice and fear. Good answers should discuss how their common interest helped them see past their differences and form a connection.",
        "book_reference": "Chelsea's Story, Part 5"
    },
    {
        "id": "q101_b2_sequence",
        "character_id": "101",
        "language_level": "B2",
        "question": "The moment when Chelsea lost her magnifying glass set off a chain of events that changed her perspective. How did this seemingly simple incident lead to such significant changes in her understanding of others?",
        "context": "The lost magnifying glass created an opportunity for unexpected interaction, leading to changed perspectives and personal growth. Good answers should trace how this incident initiated a sequence of events that transformed Chelsea's understanding of prejudice and kindness.",
        "book_reference": "Chelsea's Story, Part 6"
    },

    # Chelsea Wellington (character_id: 101) - C1 Level Questions
    {
        "id": "q101_c1_character",
        "character_id": "101",
        "language_level": "C1",
        "question": "To what extent does Agnes's discovery of the magnifying glass serve as a metaphor for seeing beyond surface appearances? Consider how this moment challenges both Chelsea's and the reader's preconceptions.",
        "context": "The incident symbolically represents the theme of looking beneath surface appearances, with Agnes demonstrating humanity and kindness despite her circumstances. Good answers should analyze both the literal and metaphorical significance of this encounter, discussing how it challenges societal prejudices.",
        "book_reference": "Chelsea's Story, Part 1"
    },
    {
        "id": "q101_c1_setting",
        "character_id": "101",
        "language_level": "C1",
        "question": "In what ways does the park setting serve as a microcosm of larger social dynamics? Consider how this public space facilitates encounters that might not occur in more structured environments.",
        "context": "The park represents a space where social boundaries blur and different worlds intersect, enabling unexpected encounters and challenging social hierarchies. Good answers should analyze how the setting's nature as a public space enables both physical and social exploration.",
        "book_reference": "Chelsea's Story, Part 2"
    },
    {
        "id": "q101_c1_cause_effect",
        "character_id": "101",
        "language_level": "C1",
        "question": "How do Chelsea and Leo's initial reactions to Agnes reflect broader societal attitudes toward marginalized individuals? Consider both conscious and unconscious factors influencing their behavior.",
        "context": "Their reaction embodies internalized societal prejudices, childhood psychological development, and learned social behaviors. Good answers should analyze the complex interplay of personal, psychological, and societal factors in their response.",
        "book_reference": "Chelsea's Story, Part 3"
    },
    {
        "id": "q101_c1_classifying",
        "character_id": "101",
        "language_level": "C1",
        "question": "How might we interpret Chelsea's Adventure Kit as a metaphor for different approaches to understanding the world? Choose one item and explore its symbolic significance in depth.",
        "context": "Each tool represents different ways of engaging with and understanding reality: detailed observation (magnifying glass), documentation (notebook), exploration (flashlight). Good answers should provide sophisticated analysis of how a chosen item represents broader themes of discovery and understanding.",
        "book_reference": "Chelsea's Story, Part 4"
    },
    {
        "id": "q101_c1_comparing",
        "character_id": "101",
        "language_level": "C1",
        "question": "How does the shared interest in entomology between Chelsea and Agnes transcend social barriers? Consider how this common ground challenges societal assumptions about connection and understanding.",
        "context": "Their mutual interest creates a neutral space for connection that transcends social categories and prejudices. Good answers should analyze how shared intellectual curiosity can overcome social barriers and challenge assumptions about who can share meaningful connections.",
        "book_reference": "Chelsea's Story, Part 5"
    },
    {
        "id": "q101_c1_sequence",
        "character_id": "101",
        "language_level": "C1",
        "question": "How does the loss of the magnifying glass function as a catalyst for Chelsea's moral and social development? Consider both the immediate consequences and broader implications of this incident.",
        "context": "The incident serves as both plot device and metaphor, initiating a journey of moral development and social awareness. Good answers should analyze how this event triggers both external plot developments and internal character growth.",
        "book_reference": "Chelsea's Story, Part 6"
    },
    # Archie (character_id: 102) - A2 Level Questions
    {
        "id": "q102_a2_1",
        "character_id": "102",
        "language_level": "A2",
        "question": "Can you tell me about the main dinosaur in our story? What was special about him?",
        "context": "The story centers around Archie, a dinosaur with unique characteristics. Good answers should identify Archie and mention something distinctive about him.",
        "book_reference": "Archie's Story, Intro"
    },
    {
        "id": "q102_a2_2",
        "character_id": "102",
        "language_level": "A2",
        "question": "Archie had a big club on his tail that made him nervous. Why do you think he felt this way about his tail?",
        "context": "Archie was uncomfortable with his tail club because it often caused accidents and made him feel clumsy. Good answers should explain his feelings and connect them to the problems his tail caused.",
        "book_reference": "Archie's Story, Chapter 1"
    },
    {
        "id": "q102_a2_3",
        "character_id": "102",
        "language_level": "A2",
        "question": "Tell me about Archie's friend Stu. What kind of friend was he to Archie?",
        "context": "Stu was Archie's friend who spent time with him despite his clumsiness. Good answers should mention Stu and describe something about their friendship.",
        "book_reference": "Archie's Story, Chapter 2"
    },
    {
        "id": "q102_a2_4",
        "character_id": "102",
        "language_level": "A2",
        "question": "Archie often said sorry to other dinosaurs. What usually happened that made him need to apologize?",
        "context": "Archie frequently apologized because his tail club would accidentally cause problems or bump into things. Good answers should explain the connection between his tail and his apologies.",
        "book_reference": "Archie's Story, Chapter 3"
    },

    # Archie (character_id: 102) - B1 Level Questions
    {
        "id": "q102_b1_1",
        "character_id": "102",
        "language_level": "B1",
        "question": "What challenges did Archie face because of his unique physical characteristic? How did these challenges affect his daily life?",
        "context": "Archie struggled with his tail club, which caused accidents and social difficulties. Good answers should discuss how this physical feature impacted both his actions and his relationships with others.",
        "book_reference": "Archie's Story, Intro"
    },
    {
        "id": "q102_b1_2",
        "character_id": "102",
        "language_level": "B1",
        "question": "Describe the relationship between Archie and his tail club. Why was it both a source of worry and potentially useful?",
        "context": "While Archie's tail club caused him anxiety and accidents, it had potential strength and usefulness. Good answers should explore this dual nature of his physical feature.",
        "book_reference": "Archie's Story, Chapter 1"
    },
    {
        "id": "q102_b1_3",
        "character_id": "102",
        "language_level": "B1",
        "question": "How did Stu's friendship help Archie deal with his insecurities? What made their friendship special?",
        "context": "Stu provided support and acceptance despite Archie's clumsiness and self-doubt. Good answers should discuss aspects of their friendship and its importance to Archie.",
        "book_reference": "Archie's Story, Chapter 2"
    },
    {
        "id": "q102_b1_4",
        "character_id": "102",
        "language_level": "B1",
        "question": "Why did Archie feel the need to apologize so often? How did this affect his confidence and relationships with others?",
        "context": "Archie's frequent apologies stemmed from accidents with his tail, affecting his self-image and social interactions. Good answers should explore both the practical and emotional aspects of this situation.",
        "book_reference": "Archie's Story, Chapter 3"
    },

    # Archie (character_id: 102) - B2 Level Questions
    {
        "id": "q102_b2_1",
        "character_id": "102",
        "language_level": "B2",
        "question": "Throughout the story, Archie's tail club seems to represent both his greatest challenge and his unique strength. How does this physical characteristic shape his journey of self-discovery?",
        "context": "The tail club serves as both a physical and metaphorical element in Archie's development, representing his struggles with self-acceptance and hidden potential. Good answers should analyze how this feature influences his character growth.",
        "book_reference": "Archie's Story, Intro"
    },
    {
        "id": "q102_b2_2",
        "character_id": "102",
        "language_level": "B2",
        "question": "Consider how Archie's perception of his tail club evolves throughout the story. What does this tell us about accepting our perceived flaws?",
        "context": "Archie's relationship with his tail club changes from fear and embarrassment to eventual acceptance and appreciation. Good answers should explore this transformation and its broader implications about self-acceptance.",
        "book_reference": "Archie's Story, Chapter 1"
    },
    {
        "id": "q102_b2_3",
        "character_id": "102",
        "language_level": "B2",
        "question": "How does Stu's acceptance of Archie, despite his differences, demonstrate the true nature of friendship? What can we learn from their relationship?",
        "context": "Stu's friendship represents unconditional acceptance and support, contrasting with others' reactions to Archie's clumsiness. Good answers should analyze the deeper aspects of their friendship and its broader messages.",
        "book_reference": "Archie's Story, Chapter 2"
    },
    {
        "id": "q102_b2_4",
        "character_id": "102",
        "language_level": "B2",
        "question": "Archie's habit of apologizing reflects deeper issues about self-image and social acceptance. How does this recurring element in the story highlight broader themes about fitting in?",
        "context": "The constant apologies represent Archie's struggle with social acceptance and self-worth. Good answers should examine how this behavior reflects broader themes about belonging and self-acceptance.",
        "book_reference": "Archie's Story, Chapter 3"
    },

    # Archie (character_id: 102) - C1 Level Questions
    {
        "id": "q102_c1_1",
        "character_id": "102",
        "language_level": "C1",
        "question": "To what extent does Archie's physical difference serve as a metaphor for broader themes of diversity and self-acceptance? Consider how his story challenges conventional narratives about disability and difference.",
        "context": "Archie's tail club represents physical difference and perceived disability, while also challenging assumptions about what constitutes a limitation versus a strength. Good answers should provide sophisticated analysis of these themes and their broader implications.",
        "book_reference": "Archie's Story, Intro"
    },
    {
        "id": "q102_c1_2",
        "character_id": "102",
        "language_level": "C1",
        "question": "Analyze how the narrative transforms Archie's tail club from a source of shame to a symbol of unique potential. How does this transformation reflect broader societal attitudes toward difference?",
        "context": "The story's treatment of Archie's tail club challenges preconceptions about physical differences and abilities. Good answers should examine how this transformation comments on societal attitudes and personal growth.",
        "book_reference": "Archie's Story, Chapter 1"
    },
    {
        "id": "q102_c1_3",
        "character_id": "102",
        "language_level": "C1",
        "question": "How does the friendship between Archie and Stu serve to deconstruct conventional narratives about difference and acceptance? Consider the broader implications for social inclusion.",
        "context": "Their friendship challenges typical narratives about difference and acceptance, offering insights into genuine inclusion and understanding. Good answers should analyze how their relationship comments on broader social dynamics.",
        "book_reference": "Archie's Story, Chapter 2"
    },
    {
        "id": "q102_c1_4",
        "character_id": "102",
        "language_level": "C1",
        "question": "Examine how Archie's pattern of apologizing reflects internalized societal attitudes toward difference. How does this aspect of the story critique broader social expectations about conformity?",
        "context": "Archie's apologetic behavior represents internalized social pressure and expectations about conformity. Good answers should analyze how this element of the story comments on broader social attitudes toward difference and acceptance.",
        "book_reference": "Archie's Story, Chapter 3"
    }
]