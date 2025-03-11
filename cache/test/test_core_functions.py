import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Ajout du répertoire parent au chemin pour pouvoir importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des modules à tester
from core.utils import chunk_text, create_chapters_from_segments, export_text_file
from core.error_handling import handle_error, ErrorType
from core.gpt_processor import extract_keywords


class TestUtils(unittest.TestCase):
    """Tests pour les fonctions utilitaires."""

    def test_chunk_text(self):
        """Test de la fonction de découpage de texte."""
        # Test avec un texte court
        short_text = "Ceci est un test."
        chunks = chunk_text(short_text, max_chars=50)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)

        # Test avec un texte long
        long_text = "A" * 100
        chunks = chunk_text(long_text, max_chars=30)
        self.assertEqual(len(chunks), 4)
        self.assertEqual(len(chunks[0]), 30)
        self.assertEqual(len(chunks[1]), 30)
        self.assertEqual(len(chunks[2]), 30)
        self.assertEqual(len(chunks[3]), 10)

        # Test avec max_chars à zéro ou négatif
        with self.assertRaises(ValueError):
            chunk_text("Test", max_chars=0)

        # Test avec texte vide
        chunks = chunk_text("", max_chars=10)
        self.assertEqual(len(chunks), 0)

    def test_create_chapters_from_segments(self):
        """Test de la fonction de création de chapitres."""
        # Segments de test
        segments = [
            {"start": 0.0, "end": 10.0, "text": "Premier segment."},
            {"start": 10.0, "end": 20.0, "text": "Deuxième segment."},
            {"start": 20.0, "end": 30.0, "text": "Troisième segment."},
            {"start": 70.0, "end": 80.0, "text": "Segment plus tard."}
        ]

        # Test avec durée de chapitre de 60 secondes
        chapters = create_chapters_from_segments(segments, chunk_duration=60)
        self.assertEqual(len(chapters), 2)
        self.assertIn("Chapitre 1", chapters[0])
        self.assertIn("Chapitre 2", chapters[1])

        # Test avec liste vide
        empty_chapters = create_chapters_from_segments([])
        self.assertEqual(len(empty_chapters), 0)

        # Test avec durée très courte (chaque segment devient un chapitre)
        short_chapters = create_chapters_from_segments(segments, chunk_duration=5)
        self.assertEqual(len(short_chapters), 4)

    def test_export_text_file(self):
        """Test de la fonction d'export de fichier texte."""
        text = "Contenu du fichier de test."

        # Test avec dossier temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = export_text_file(text, temp_dir, "test.txt")

            # Vérifier que le fichier existe
            self.assertTrue(os.path.exists(out_path))

            # Vérifier le contenu
            with open(out_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertEqual(content, text)

        # Test avec texte vide
        with tempfile.TemporaryDirectory() as temp_dir:
            result = export_text_file("", temp_dir, "empty.txt")
            self.assertEqual(result, "")


class TestErrorHandling(unittest.TestCase):
    """Tests pour les fonctions de gestion d'erreurs."""

    @patch('logging.error')
    def test_handle_error(self, mock_logging):
        """Test de la fonction de gestion d'erreurs."""
        # Créer une erreur de test
        test_error = ValueError("Erreur de test")

        # Tester avec mock pour logger
        error_message = handle_error(
            test_error,
            ErrorType.PROCESSING_ERROR,
            "Message utilisateur"
        )

        # Vérifier que logging.error a été appelé
        mock_logging.assert_called_once()

        # Vérifier le message retourné
        self.assertEqual(error_message, "Message utilisateur")

        # Tester sans message personnalisé
        with patch('logging.error'):
            error_message = handle_error(
                test_error,
                ErrorType.API_ERROR
            )
            self.assertIn("API", error_message)


class TestGPTProcessor(unittest.TestCase):
    """Tests pour les fonctions de traitement GPT."""

    @patch('core.gpt_processor.gpt_request')
    def test_extract_keywords(self, mock_gpt_request):
        """Test de la fonction d'extraction de mots-clés."""
        # Configuration du mock
        mock_gpt_request.return_value = "mot-clé1, mot-clé2, mot-clé3"

        # Appel de la fonction
        result = extract_keywords("Texte de test.", "fake_api_key")

        # Vérifications
        self.assertEqual(result, "mot-clé1, mot-clé2, mot-clé3")
        mock_gpt_request.assert_called_once()

        # Test avec texte vide
        with self.assertRaises(ValueError):
            extract_keywords("", "fake_api_key")


if __name__ == "__main__":
    unittest.main()