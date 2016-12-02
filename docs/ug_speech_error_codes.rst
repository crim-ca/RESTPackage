.. _speech_error_codes:

Transcription, diarisation and text matching services error codes
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

====    ===========
Code    Description
====    ===========
630     Diarization cannot resolve the path to the audio file.
631     Audio file format is not supported by diarization process. (WAV file
        parameters)
632     WAV file header has an unsupported structure for diarization process.
633     Internal error while forking diarization subprocesses.
64x     are reserved for the Transcription service
640     Transcription worker cannot resolve path to the audio file.
641     Transcription worker encountered audio segments of greater length than
        it's capacity.
642     Transcription worker encountered an internal error while forking
        internal subprocesses.
643     Transcription worker could not produce a transcription for a given
        document.
====    ===========
