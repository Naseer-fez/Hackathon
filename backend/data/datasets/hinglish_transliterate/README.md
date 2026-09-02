---
license: cc-by-sa-4.0
task_categories:
- translation
language:
- hi
- en
tags:
- hinglish
- transliteration
- hindi
- autoscientist
- adaption
- asr-error-correction
size_categories:
- 10K<n<100K
---

# Adaption Hinglish Transliterate Dataset

## Dataset Description

This dataset contains **77,471 pairs** of raw Hindi text captured via Automatic Speech Recognition (ASR) in Devanagari script and their corresponding clean transliterations into Romanized Hinglish. The samples demonstrate the correction of ASR artifacts and the application of Anglicized Hinglish conventions while preserving the original meaning. 

Each entry consists of an original system prompt instructing the transliteration task and the resulting cleaned Roman script output, along with corresponding enhanced versions produced using [Adaption's data pipeline](https://adaptionlabs.ai/blog/adaption-launches-adaptive-data-beta).  

This dataset was created as a submission to the **[AutoScientist Challenge](https://adaptionlabs.ai/blog/autoscientist-challenge)** in the Language Category.

### Model Fine-Tuning
This dataset was used to fine-tune the [Adaption Hinglish Transliterate LoRA](https://huggingface.co/bingbangboom/adaption-hinglish-transliterate-LoRA) adapter for the Qwen3.5-0.8B base model.

## Dataset Structure

- **Total Rows**: 77,471
- **Format**: JSONL

## Dataset Construction & Sources

The was created by merging and augmenting, two primary source datasets through Adaption's data pipeline:

1. **[bingbangboom/tiny-aya-translate-hinglish-casual-stripped](https://huggingface.co/datasets/bingbangboom/tiny-aya-translate-hinglish-casual-stripped)** 
   - **License**: MIT
   - **Details**: Used as a base for augmented conversational Hinglish translations.
2. **[bingbangboom/cleaned-asr-transcripts-hinglish](https://huggingface.co/datasets/bingbangboom/cleaned-asr-transcripts-hinglish)** 
   - **License**: CC BY-SA 4.0
   - **Details**: A parallel corpus containing 14k+ pairs of raw-synthetic Hindi ASR transcripts mapped to their clean, properly punctuated, and transliterated "Hinglish" counterparts. Specifically designed for ASR post-processing and transliteration models.

![Metrics](images/metrics.png)

## License

This dataset is distributed under the **[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)** (Creative Commons Attribution-ShareAlike 4.0 International) license.