"""Minimal context-aware hint policy for the user-improved bie2 control.

This is a text-side CosyVoice3 input adapter, not ASR correction or a validated
phonetic evaluator. Other readings remain Hanzi; no source-speaker registration.
"""
from importlib.metadata import version
from pypinyin import pinyin, Style


def prepare_text(text: str) -> dict:
    readings = pinyin(text, style=Style.TONE, heteronym=False,
                      errors=lambda chars: list(chars))
    if len(readings) != len(text):
        raise ValueError("Contextual pronunciation did not preserve character positions")
    parts, spans = [], []
    for index, (char, candidates) in enumerate(zip(text, readings)):
        reading = candidates[0]
        # Only bie2 has a positive user listening comparison. In particular,
        # don't force bie2 for 别扭/别拗, and don't force every 这/是: that test
        # changed rhythm markedly. A reading dictionary is itself fallible.
        # The installed dictionary fell back to bie2 on 别拗 in the regression
        # check. Conservatively leave these contexts untouched, regardless of
        # what the dictionary returns; this is not a claim of a complete lexicon.
        guarded_context = any(text.startswith(word, index)
                              for word in ('别扭', '别拗'))
        replacement = '[b][ié]' if char == '别' and reading == 'bié' and not guarded_context else char
        parts.append(replacement)
        if replacement != char:
            spans.append(dict(character_index=index, original=char,
                              contextual_reading=reading, model_hint=replacement))
    return dict(original_text=text, model_text=''.join(parts), hints=spans,
                pypinyin_version=version('pypinyin'),
                recognized_text_rewritten=False,
                dictionary_pronunciations_not_human_gold=True,
                unreviewed_other_readings_left_unchanged=True,
                source_speaker_enrollment=False,
                pronunciation_automatically_accepted=False)
