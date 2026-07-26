from credit_engine.encoding import (
    EXCLUDED_COLS,
    MULTILABEL_COLS,
    NUMERIC_COLS,
    ONEHOT_COLS,
    ORDINAL_COLS,
    ORDINAL_ORDER,
    TARGET_COL,
)


class TestNumericCols:
    def test_contains_seven_features(self):
        assert len(NUMERIC_COLS) == 7

    def test_excludes_target_column(self):
        assert TARGET_COL not in NUMERIC_COLS

    def test_excludes_excluded_columns(self):
        for col in EXCLUDED_COLS:
            assert col not in NUMERIC_COLS


class TestOnehotCols:
    def test_contains_exactly_one_column(self):
        assert len(ONEHOT_COLS) == 1

    def test_column_is_categoria_afiliacion(self):
        assert "categoria_afiliacion" in ONEHOT_COLS


class TestOrdinalCols:
    def test_contains_exactly_one_column(self):
        assert len(ORDINAL_COLS) == 1

    def test_column_is_mora_maxima_historica(self):
        assert "mora_maxima_historica" in ORDINAL_COLS


class TestOrdinalOrder:
    def test_has_one_category_list(self):
        assert len(ORDINAL_ORDER) == 1

    def test_four_levels_in_correct_order(self):
        assert ORDINAL_ORDER[0] == ["0_DIAS", "30_DIAS", "60_DIAS", "90_MAS_DIAS"]


class TestMultilabelCols:
    def test_contains_six_columns(self):
        assert len(MULTILABEL_COLS) == 6

    def test_includes_expected_multilabel_fields(self):
        expected = {
            "area_trabajo",
            "intereses",
            "preferencias",
            "momentos_clave",
            "composicion_familiar",
            "historial_creditos",
        }
        assert set(MULTILABEL_COLS) == expected


class TestTargetCol:
    def test_target_is_producto_colsubsidio_target(self):
        assert TARGET_COL == "producto_colsubsidio_target"


class TestExcludedCols:
    def test_contains_pii_and_contact_columns(self):
        assert len(EXCLUDED_COLS) == 8

    def test_includes_personal_identifiers(self):
        expected = {
            "cedula",
            "nombre",
            "correo",
            "direccion",
            "fecha_nacimiento",
            "telefono",
            "consent_whatsapp",
            "consent_email",
        }
        assert set(EXCLUDED_COLS) == expected


class TestNoOverlapBetweenGroups:
    def test_numeric_and_onehot_disjoint(self):
        assert set(NUMERIC_COLS).isdisjoint(set(ONEHOT_COLS))

    def test_numeric_and_ordinal_disjoint(self):
        assert set(NUMERIC_COLS).isdisjoint(set(ORDINAL_COLS))

    def test_numeric_and_multilabel_disjoint(self):
        assert set(NUMERIC_COLS).isdisjoint(set(MULTILABEL_COLS))

    def test_onehot_and_ordinal_disjoint(self):
        assert set(ONEHOT_COLS).isdisjoint(set(ORDINAL_COLS))

    def test_onehot_and_multilabel_disjoint(self):
        assert set(ONEHOT_COLS).isdisjoint(set(MULTILABEL_COLS))

    def test_ordinal_and_multilabel_disjoint(self):
        assert set(ORDINAL_COLS).isdisjoint(set(MULTILABEL_COLS))

    def test_all_groups_disjoint_from_excluded(self):
        all_features = set(NUMERIC_COLS) | set(ONEHOT_COLS) | set(ORDINAL_COLS) | set(MULTILABEL_COLS) | {TARGET_COL}
        assert all_features.isdisjoint(set(EXCLUDED_COLS))
