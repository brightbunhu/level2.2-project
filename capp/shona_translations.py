# Dictionary mapping English phrases to Shona translations
SHONA_TRANSLATIONS = {
    # Greetings and Common Phrases
    'hello': 'mhoro',
    'hi': 'mhoro',
    'good morning': 'mangwanani',
    'good afternoon': 'masikati',
    'good evening': 'manheru',
    'how are you': 'makadii',
    'i am fine': 'ndiri bho',
    'we are fine': 'tiri bho',
    'we are very happy': 'tinofara zvikuru',
    'we are happy': 'tinofara',
    'we thank you': 'tinotenda',
    'thank you': 'ndinotenda',
    'we': 'tino',
    'are': 'ri',
    'happy': 'fara',
    'very': 'zvikuru',
    'thank': 'tenda',
    
    # Common Words and Particles
    'tino': 'we',
    'ndino': 'i',
    'vano': 'they',
    'ano': 'he/she',
    'fara': 'happy',
    'tenda': 'thank',
    'nzwisisa': 'understand',
    'basa': 'work',
    'mhuri': 'family',
    'rudo': 'love',
    'bho': 'fine/okay',
    'zvikuru': 'very much',
    
    # Verb Prefixes
    'ndiri': 'i am',
    'tiri': 'we are',
    'vari': 'they are',
    'ari': 'he/she is',
    'ndino': 'i do',
    'tino': 'we do',
    'vano': 'they do',
    'ano': 'he/she does',
    
    # Full Phrases
    'tinofara': 'we are happy',
    'tinotenda': 'we thank you',
    'tinofara zvikuru': 'we are very happy',
    'tinotenda zvikuru': 'we thank you very much',
}

def translate_to_shona(text):
    """
    Translate English text to Shona using the dictionary
    """
    text = text.lower().strip()
    
    # Check for exact match
    if text in SHONA_TRANSLATIONS:
        return SHONA_TRANSLATIONS[text]
        
    # Split into words and translate each
    words = text.split()
    translated_words = []
    
    i = 0
    while i < len(words):
        translated = False
        
        # Try to match phrases of decreasing length
        for j in range(min(4, len(words) - i), 0, -1):
            phrase = ' '.join(words[i:i+j])
            if phrase in SHONA_TRANSLATIONS:
                translated_words.append(SHONA_TRANSLATIONS[phrase])
                i += j
                translated = True
                break
        
        if not translated:
            translated_words.append(words[i])
            i += 1
    
    return ' '.join(translated_words)

def translate_from_shona(text):
    """
    Translate Shona text to English using reverse dictionary lookup
    """
    text = text.lower().strip()
    
    # Create reverse dictionary
    reverse_dict = {v: k for k, v in SHONA_TRANSLATIONS.items()}
    
    # Check for exact match
    if text in reverse_dict:
        return reverse_dict[text]
    
    # Split into words and translate each
    words = text.split()
    translated_words = []
    
    i = 0
    while i < len(words):
        translated = False
        
        # Try to match phrases of decreasing length
        for j in range(min(4, len(words) - i), 0, -1):
            phrase = ' '.join(words[i:i+j])
            if phrase in reverse_dict:
                translated_words.append(reverse_dict[phrase])
                i += j
                translated = True
                break
                
        # Try to match verb prefixes
        if not translated and len(words[i]) >= 4:
            prefix = words[i][:4]  # Get first 4 letters
            if prefix in reverse_dict:
                # Handle verb prefixes
                translated_words.append(reverse_dict[prefix])
                if len(words[i]) > 4:
                    # Add the rest of the word if there's more
                    rest = words[i][4:]
                    if rest in reverse_dict:
                        translated_words.append(reverse_dict[rest])
                    else:
                        translated_words.append(rest)
                i += 1
                translated = True
        
        if not translated:
            # Check if word exists in reverse translations
            if words[i] in reverse_dict:
                translated_words.append(reverse_dict[words[i]])
            else:
                translated_words.append(words[i])
            i += 1
    
    # Clean up the translation
    translation = ' '.join(translated_words)
    
    # Common post-processing fixes
    common_fixes = {
        'we do happy': 'we are happy',
        'we do thank you': 'we thank you',
        'i do happy': 'i am happy',
        'they do happy': 'they are happy',
    }
    
    for wrong, right in common_fixes.items():
        translation = translation.replace(wrong, right)
    
    return translation