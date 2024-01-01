import tensorflow as tf
import pandas as pd
from utils.fnProcessing import read_config, pad_punctuation, normalize_text, remove_whitespace

config_params = read_config(section='params', config_path='./generative_text/configkeras.ini')
params = {key: config_params[key] for key in config_params}

def prepare_data(data, input_col, clean_col):
    data[input_col] = data[input_col].astype(str)
    data[clean_col] = data[input_col].apply(normalize_text).apply(remove_whitespace).apply(pad_punctuation)
    return data[data[clean_col].notnull() & data[clean_col].str.strip().astype(bool)]

def get_datasets(text_data):
    batch_size =  int(params['batch_size'])
    validation_split = float(params['validation_split'])

    text_data = tf.data.Dataset.from_tensor_slices(text_data)
    n_samples = sum(1 for _ in text_data)
    n_train_samples = int(n_samples * float(1 - validation_split))
    n_val_samples = int(n_samples * validation_split)
    train_text_ds = text_data.take(n_train_samples)
    val_text_ds = text_data.skip(n_train_samples).take(n_val_samples)
    test_text_ds = text_data.skip(n_train_samples + n_val_samples)
    train_text_ds = train_text_ds.batch(batch_size).shuffle(buffer_size=n_train_samples)
    val_text_ds = val_text_ds.batch(batch_size).shuffle(buffer_size=n_val_samples)
    test_text_ds = test_text_ds.batch(batch_size).shuffle(buffer_size=n_samples - n_train_samples - n_val_samples)
    return train_text_ds, val_text_ds, test_text_ds

def main(data, input_col='text', clean_col='text'):
    max_len = int(params['max_len'])
    vocab_size = int(params['vocab_size'])
    data[input_col] = data[input_col].astype(str)
    data[clean_col] = data[input_col].apply(normalize_text).apply(remove_whitespace).apply(pad_punctuation)
    return data[data[clean_col].notnull() & data[clean_col].str.strip().astype(bool)]

    vectorize_layer = tf.keras.layers.TextVectorization(
        standardize=None,
        max_tokens=vocab_size,
        output_mode="int",
        output_sequence_length=max_len + 1
    )

    train_text_ds, val_text_ds, test_text_ds = get_datasets(text_data)
    vectorize_layer.adapt(train_text_ds)

    def prepare_lm_inputs_labels(text):
        text = tf.expand_dims(text, -1)
        tokenized_sentences = vectorize_layer(text)
        x = tokenized_sentences[:, :-1]
        y = tokenized_sentences[:, 1:]
        return x, y

    train_ds = train_text_ds.map(prepare_lm_inputs_labels)
    val_ds = val_text_ds.map(prepare_lm_inputs_labels)
    test_ds = test_text_ds.map(prepare_lm_inputs_labels)

    train_ds = train_ds.prefetch(tf.data.AUTOTUNE)
    val_ds = val_ds.prefetch(tf.data.AUTOTUNE)
    test_ds = test_ds.prefetch(tf.data.AUTOTUNE)

    vocab = vectorize_layer.get_vocabulary()
    return train_ds, val_ds, test_ds, vocab

if __name__ == "__main__":
    train_ds, val_ds, test_ds, vocab = main(training_data, input_col='text', clean_col='text')