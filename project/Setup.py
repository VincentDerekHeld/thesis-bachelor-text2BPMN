import benepar


def download_all_dependencies():
    import nltk
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    benepar.download('benepar_en3')
    benepar.download('benepar_en3_large')
    nltk.download('wordnet')