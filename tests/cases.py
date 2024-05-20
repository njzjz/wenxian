"""Test cases."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

from wenxian.reference import Author, Reference


@dataclass
class ReferenceCase:
    """Test case for a reference."""

    reference: Reference
    expected_bibtex: str
    pmid: int | None = None
    arxiv: str | None = None


TEST_CASES = [
    # mainly from pubmed
    ReferenceCase(
        reference=Reference(
            author=[
                Author(first="Jinzhe", last="Zeng"),
                Author(first="Yujun", last="Tao"),
                Author(first="Timothy J.", last="Giese"),
                Author(first="Darrin M.", last="York"),
            ],
            title="QDπ: A Quantum Deep Potential Interaction Model for Drug Discovery",
            journal="Journal of chemical theory and computation",
            year=2023,
            volume=19,
            issue=4,
            pages=(1261, 1275),
            annote=textwrap.dedent(
                """\
            We report QDπ-v1.0 for modeling the internal energy of drug molecules
            containing H, C, N, and O atoms. The QDπ model is in the form of a
            quantum mechanical/machine learning potential correction (QM/Δ-MLP)
            that uses a fast third-order self-consistent density-functional
            tight-binding (DFTB3/3OB) model that is corrected to a quantitatively
            high-level of accuracy through a deep-learning potential (DeepPot-SE).
            The model has the advantage that it is able to properly treat
            electrostatic interactions and handle changes in charge/protonation
            states. The model is trained against reference data computed at the
            ωB97X/6-31G* level (as in the ANI-1x data set) and compared to several
            other approximate semiempirical and machine learning potentials
            (ANI-1x, ANI-2x, DFTB3, MNDO/d, AM1, PM6, GFN1-xTB, and GFN2-xTB). The
            QDπ model is demonstrated to be accurate for a wide range of intra- and
            intermolecular interactions (despite its intended use as an internal
            energy model) and has shown to perform exceptionally well for relative
            protonation/deprotonation energies and tautomers. An example application
            to model reactions involved in RNA strand cleavage catalyzed by protein
            and nucleic acid enzymes illustrates QDπ has average errors less than
            0.5 kcal/mol, whereas the other models compared have errors over an
            order of magnitude greater. Taken together, this makes QDπ highly
            attractive as a potential force field model for drug discovery.
            """
            )
            .strip()
            .replace("\n", " "),
            doi="10.1021/acs.jctc.2c01172",
        ),
        expected_bibtex=textwrap.dedent(r"""
        @Article{Zeng_JChemTheoryComput_2023_v19_p1261,
            author =   {Jinzhe Zeng and Yujun Tao and Timothy J. Giese and Darrin M. York},
            title =    {{QD{\ensuremath{\pi}}: A Quantum Deep Potential Interaction Model for
                     Drug Discovery}},
            journal =  {J. Chem. Theory Comput.},
            year =     2023,
            volume =   19,
            issue =    4,
            pages =    {1261--1275},
            doi =      {10.1021/acs.jctc.2c01172},
            annote =   {We report QD{\ensuremath{\pi}}-v1.0 for modeling the internal energy
                     of drug molecules containing H, C, N, and O atoms. The
                     QD{\ensuremath{\pi}} model is in the form of a quantum
                     mechanical/machine learning potential correction
                     (QM/{\ensuremath{\Delta}}-MLP) that uses a fast third-order self-
                     consistent density-functional tight-binding (DFTB3/3OB) model that is
                     corrected to a quantitatively high-level of accuracy through a deep-
                     learning potential (DeepPot-SE). The model has the advantage that it
                     is able to properly treat electrostatic interactions and handle
                     changes in charge/protonation states. The model is trained against
                     reference data computed at the {\ensuremath{\omega}}B97X/6-31G* level
                     (as in the ANI-1x data set) and compared to several other approximate
                     semiempirical and machine learning potentials (ANI-1x, ANI-2x, DFTB3,
                     MNDO/d, AM1, PM6, GFN1-xTB, and GFN2-xTB). The QD{\ensuremath{\pi}}
                     model is demonstrated to be accurate for a wide range of intra- and
                     intermolecular interactions (despite its intended use as an internal
                     energy model) and has shown to perform exceptionally well for relative
                     protonation/deprotonation energies and tautomers. An example
                     application to model reactions involved in RNA strand cleavage
                     catalyzed by protein and nucleic acid enzymes illustrates
                     QD{\ensuremath{\pi}} has average errors less than 0.5 kcal/mol,
                     whereas the other models compared have errors over an order of
                     magnitude greater. Taken together, this makes QD{\ensuremath{\pi}}
                     highly attractive as a potential force field model for drug discovery.},
        }
    """).strip(),
        pmid=36696673,
    ),
    # no records in PubMed, mainly from crossref
    ReferenceCase(
        reference=Reference(
            author=[
                Author(first="Yuzhi", last="Zhang"),
                Author(first="Haidi", last="Wang"),
                Author(first="Weijie", last="Chen"),
                Author(first="Jinzhe", last="Zeng"),
                Author(first="Linfeng", last="Zhang"),
                Author(first="Han", last="Wang"),
                Author(first="Weinan", last="E"),
            ],
            title="DP-GEN: A concurrent learning platform for the generation of reliable deep learning based potential energy models",
            journal="Computer Physics Communications",
            year=2020,
            volume=253,
            pages=(107206,),
            doi="10.1016/j.cpc.2020.107206",
        ),
        expected_bibtex=textwrap.dedent(r"""
            @Article{Zhang_ComputPhysCommun_2020_v253_p107206,
                author =   {Yuzhi Zhang and Haidi Wang and Weijie Chen and Jinzhe Zeng and Linfeng
                         Zhang and Han Wang and Weinan E},
                title =    {{DP-GEN: A concurrent learning platform for the generation of reliable
                         deep learning based potential energy models}},
                journal =  {Comput. Phys. Commun.},
                year =     2020,
                volume =   253,
                pages =    107206,
                doi =      {10.1016/j.cpc.2020.107206},
            }""").strip(),
    ),
    # arXiv
    ReferenceCase(
        reference=Reference(
            author=[
                Author(first="Yuzhi", last="Zhang"),
                Author(first="Haidi", last="Wang"),
                Author(first="Weijie", last="Chen"),
                Author(first="Jinzhe", last="Zeng"),
                Author(first="Linfeng", last="Zhang"),
                Author(first="Han", last="Wang"),
                Author(first="Weinan", last="E"),
            ],
            title="DP-GEN: A concurrent learning platform for the generation of reliable deep learning based potential energy models",
            journal="arXiv",
            year=2019,
            pages="1910.12690",
            doi="10.48550/arXiv.1910.12690",
            annote=textwrap.dedent("""\
                In recent years, promising deep learning based interatomic potential
                energy surface (PES) models have been proposed that can potentially
                allow us to perform molecular dynamics simulations for large scale
                systems with quantum accuracy. However, making these models truly
                reliable and practically useful is still a very non-trivial task. A
                key component in this task is the generation of datasets used in model
                training. In this paper, we introduce the Deep Potential GENerator
                (DP-GEN), an open-source software platform that implements the
                recently proposed "on-the-fly" learning procedure [Phys. Rev.
                Materials 3, 023804] and is capable of generating uniformly accurate
                deep learning based PES models in a way that minimizes human
                intervention and the computational cost for data generation and model
                training. DP-GEN automatically and iteratively performs three steps:
                exploration, labeling, and training. It supports various popular
                packages for these three steps: LAMMPS for exploration, Quantum
                Espresso, VASP, CP2K, etc. for labeling, and DeePMD-kit for training.
                It also allows automatic job submission and result collection on
                different types of machines, such as high performance clusters and
                cloud machines, and is adaptive to different job management tools,
                including Slurm, PBS, and LSF. As a concrete example, we illustrate
                the details of the process for generating a general-purpose PES model
                for Cu using DP-GEN.
                """)
            .strip()
            .replace("\n", " "),
        ),
        expected_bibtex=textwrap.dedent(r"""
            @Article{Zhang_Arxivself_2019_p1910.12690,
                author =   {Yuzhi Zhang and Haidi Wang and Weijie Chen and Jinzhe Zeng and Linfeng
                        Zhang and Han Wang and Weinan E},
                title =    {{DP-GEN: A concurrent learning platform for the generation of reliable
                        deep learning based potential energy models}},
                journal =  {Arxiv},
                year =     2019,
                pages =    {1910.12690},
                doi =      {10.48550/arXiv.1910.12690},
                annote =   {In recent years, promising deep learning based interatomic potential
                        energy surface (PES) models have been proposed that can potentially
                        allow us to perform molecular dynamics simulations for large scale
                        systems with quantum accuracy. However, making these models truly
                        reliable and practically useful is still a very non-trivial task. A
                        key component in this task is the generation of datasets used in model
                        training. In this paper, we introduce the Deep Potential GENerator
                        (DP-GEN), an open-source software platform that implements the
                        recently proposed "on-the-fly" learning procedure [Phys. Rev.
                        Materials 3, 023804] and is capable of generating uniformly accurate
                        deep learning based PES models in a way that minimizes human
                        intervention and the computational cost for data generation and model
                        training. DP-GEN automatically and iteratively performs three steps:
                        exploration, labeling, and training. It supports various popular
                        packages for these three steps: LAMMPS for exploration, Quantum
                        Espresso, VASP, CP2K, etc. for labeling, and DeePMD-kit for training.
                        It also allows automatic job submission and result collection on
                        different types of machines, such as high performance clusters and
                        cloud machines, and is adaptive to different job management tools,
                        including Slurm, PBS, and LSF. As a concrete example, we illustrate
                        the details of the process for generating a general-purpose PES model
                        for Cu using DP-GEN.},
            }
            """).strip(),
        arxiv="1910.12690",
    ),
]
