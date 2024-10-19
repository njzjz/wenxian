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
            number =   4,
            pages =    {1261--1275},
            doi =      {10.1021/acs.jctc.2c01172},
            abstract = {We report QD{\ensuremath{\pi}}-v1.0 for modeling the internal energy
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
            @Article{Zhang_arXiv_2019_p1910.12690,
                author =   {Yuzhi Zhang and Haidi Wang and Weijie Chen and Jinzhe Zeng and Linfeng
                         Zhang and Han Wang and Weinan E},
                title =    {{DP-GEN: A concurrent learning platform for the generation of reliable
                         deep learning based potential energy models}},
                journal =  {arXiv},
                year =     2019,
                pages =    {1910.12690},
                doi =      {10.48550/arXiv.1910.12690},
                abstract = {In recent years, promising deep learning based interatomic potential
                         energy surface (PES) models have been proposed that can potentially
                         allow us to perform molecular dynamics simulations for large scale
                         systems with quantum accuracy. However, making these models truly
                         reliable and practically useful is still a very non-trivial task. A
                         key component in this task is the generation of datasets used in model
                         training. In this paper, we introduce the Deep Potential GENerator
                         (DP-GEN), an open-source software platform that implements the
                         recently proposed {''}on-the-fly{''} learning procedure [Phys. Rev.
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
    # test pii
    ReferenceCase(
        Reference(
            author=[
                Author(first="Jinzhe", last="Zeng"),
                Author(first="Duo", last="Zhang"),
                Author(first="Denghui", last="Lu"),
                Author(first="Pinghui", last="Mo"),
                Author(first="Zeyu", last="Li"),
                Author(first="Yixiao", last="Chen"),
                Author(first="Marián", last="Rynik"),
                Author(first="Li'ang", last="Huang"),
                Author(first="Ziyao", last="Li"),
                Author(first="Shaochen", last="Shi"),
                Author(first="Yingze", last="Wang"),
                Author(first="Haotian", last="Ye"),
                Author(first="Ping", last="Tuo"),
                Author(first="Jiabin", last="Yang"),
                Author(first="Ye", last="Ding"),
                Author(first="Yifan", last="Li"),
                Author(first="Davide", last="Tisi"),
                Author(first="Qiyu", last="Zeng"),
                Author(first="Han", last="Bao"),
                Author(first="Yu", last="Xia"),
                Author(first="Jiameng", last="Huang"),
                Author(first="Koki", last="Muraoka"),
                Author(first="Yibo", last="Wang"),
                Author(first="Junhan", last="Chang"),
                Author(first="Fengbo", last="Yuan"),
                Author(first="Sigbjørn Løland", last="Bore"),
                Author(first="Chun", last="Cai"),
                Author(first="Yinnian", last="Lin"),
                Author(first="Bo", last="Wang"),
                Author(first="Jiayan", last="Xu"),
                Author(first="Jia-Xin", last="Zhu"),
                Author(first="Chenxing", last="Luo"),
                Author(first="Yuzhi", last="Zhang"),
                Author(first="Rhys E. A.", last="Goodall"),
                Author(first="Wenshuo", last="Liang"),
                Author(first="Anurag Kumar", last="Singh"),
                Author(first="Sikai", last="Yao"),
                Author(first="Jingchao", last="Zhang"),
                Author(first="Renata", last="Wentzcovitch"),
                Author(first="Jiequn", last="Han"),
                Author(first="Jie", last="Liu"),
                Author(first="Weile", last="Jia"),
                Author(first="Darrin M.", last="York"),
                Author(first="Weinan", last="E"),
                Author(first="Roberto", last="Car"),
                Author(first="Linfeng", last="Zhang"),
                Author(first="Han", last="Wang"),
            ],
            title="DeePMD-kit v2: A software package for deep potential models",
            journal="The Journal of chemical physics",
            year=2023,
            volume=159,
            issue=5,
            pages="054801",
            doi="10.1063/5.0155600",
            annote=textwrap.dedent(
                """\
                DeePMD-kit is a powerful open-source software package that facilitates
                molecular dynamics simulations using machine learning potentials known
                as Deep Potential (DP) models. This package, which was released in
                2017, has been widely used in the fields of physics, chemistry,
                biology, and material science for studying atomistic systems. The
                current version of DeePMD-kit offers numerous advanced features, such
                as DeepPot-SE, attention-based and hybrid descriptors, the ability to
                fit tensile properties, type embedding, model deviation, DP-range
                correction, DP long range, graphics processing unit support for
                customized operators, model compression, non-von Neumann molecular
                dynamics, and improved usability, including documentation, compiled
                binary packages, graphical user interfaces, and application
                programming interfaces. This article presents an overview of the
                current major version of the DeePMD-kit package, highlighting its
                features and technical details. Additionally, this article presents a
                comprehensive procedure for conducting molecular dynamics as a
                representative application, benchmarks the accuracy and efficiency of
                different models, and discusses ongoing developments.
                """
            )
            .strip()
            .replace("\n", " "),
        ),
        expected_bibtex=textwrap.dedent(r"""
            @Article{Zeng_JChemPhys_2023_v159_p054801,
                author =   {Jinzhe Zeng and Duo Zhang and Denghui Lu and Pinghui Mo and Zeyu Li
                         and Yixiao Chen and Mari{\'a}n Rynik and Li'ang Huang and Ziyao Li and
                         Shaochen Shi and Yingze Wang and Haotian Ye and Ping Tuo and Jiabin
                         Yang and Ye Ding and Yifan Li and Davide Tisi and Qiyu Zeng and Han
                         Bao and Yu Xia and Jiameng Huang and Koki Muraoka and Yibo Wang and
                         Junhan Chang and Fengbo Yuan and Sigbj{\o}rn L{\o}land Bore and Chun
                         Cai and Yinnian Lin and Bo Wang and Jiayan Xu and Jia-Xin Zhu and
                         Chenxing Luo and Yuzhi Zhang and Rhys E. A. Goodall and Wenshuo Liang
                         and Anurag Kumar Singh and Sikai Yao and Jingchao Zhang and Renata
                         Wentzcovitch and Jiequn Han and Jie Liu and Weile Jia and Darrin M.
                         York and Weinan E and Roberto Car and Linfeng Zhang and Han Wang},
                title =    {{DeePMD-kit v2: A software package for deep potential models}},
                journal =  {J. Chem. Phys.},
                year =     2023,
                volume =   159,
                number =   5,
                pages =    054801,
                doi =      {10.1063/5.0155600},
                abstract = {DeePMD-kit is a powerful open-source software package that facilitates
                         molecular dynamics simulations using machine learning potentials known
                         as Deep Potential (DP) models. This package, which was released in
                         2017, has been widely used in the fields of physics, chemistry,
                         biology, and material science for studying atomistic systems. The
                         current version of DeePMD-kit offers numerous advanced features, such
                         as DeepPot-SE, attention-based and hybrid descriptors, the ability to
                         fit tensile properties, type embedding, model deviation, DP-range
                         correction, DP long range, graphics processing unit support for
                         customized operators, model compression, non-von Neumann molecular
                         dynamics, and improved usability, including documentation, compiled
                         binary packages, graphical user interfaces, and application
                         programming interfaces. This article presents an overview of the
                         current major version of the DeePMD-kit package, highlighting its
                         features and technical details. Additionally, this article presents a
                         comprehensive procedure for conducting molecular dynamics as a
                         representative application, benchmarks the accuracy and efficiency of
                         different models, and discusses ongoing developments.},
            }""").strip(),
    ),
    # semanticscholar abstract
    ReferenceCase(
        reference=Reference(
            author=[
                Author(first="Jinzhe", last="Zeng"),
                Author(first="Linfeng", last="Zhang"),
                Author(first="Han", last="Wang"),
                Author(first="Tong", last="Zhu"),
            ],
            title="Exploring the Chemical Space of Linear Alkane Pyrolysis via Deep Potential GENerator",
            journal="Energy Fuels",
            year=2021,
            volume=35,
            issue=1,
            pages=(762, 769),
            annote=textwrap.dedent("""\
                Reactive molecular dynamics (MD) simulation is a powerful tool to study the reaction
                mechanism of complex chemical systems. Central to the method is the potential energy
                surface (PES) that can desc...""")
            .strip()
            .replace("\n", " "),
            doi="10.1021/acs.energyfuels.0c03211",
        ),
        expected_bibtex=textwrap.dedent(r"""
            @Article{Zeng_EnergyFuels_2021_v35_p762,
                author =   {Jinzhe Zeng and Linfeng Zhang and Han Wang and Tong Zhu},
                title =    {{Exploring the Chemical Space of Linear Alkane Pyrolysis via Deep
                         Potential GENerator}},
                journal =  {Energy Fuels},
                year =     2021,
                volume =   35,
                number =   1,
                pages =    {762--769},
                doi =      {10.1021/acs.energyfuels.0c03211},
                abstract = {Reactive molecular dynamics (MD) simulation is a powerful tool to
                         study the reaction mechanism of complex chemical systems. Central to
                         the method is the potential energy surface (PES) that can desc...},
            }""").strip(),
    ),
    # ChemRxiv
    ReferenceCase(
        reference=Reference(
            author=[
                Author(first="Manyi", last="Yang"),
                Author(first="Duo", last="Zhang"),
                Author(first="Xinyan", last="Wang"),
                # why not Linfeng???
                Author(first="Lingfeng", last="Zhang"),
                Author(first="Tong", last="Zhu"),
                Author(first="Han", last="Wang"),
            ],
            title="Ab initio Accuracy Neural Network Potential for Drug-like Molecules",
            journal="ChemRxiv",
            year=2024,
            annote=textwrap.dedent("""\
                <jats:p>The advent of machine learning
                (ML) in computational chemistry heralds a transformative approach to
                one of the quintessential challenges in computer-aided drug design
                (CADD): the accurate and cost-effective calculation of atomic
                interactions. By leveraging a neural network (NN) potential, we
                address this balance and push the boundaries of the NN potential's
                representational capacity. Our work details the development of a
                robust general-purpose NN potential, architected on the framework of
                DPA-2, a deep learning potential with attention, which demonstrates
                remarkable fidelity in replicating the interatomic potential energy
                surface for drug-like molecules comprising eight critical chemical
                elements: H, C, N, O, F, S, Cl, and P. We employed state-of-the-art
                molecular dynamic techniques, including temperature acceleration and
                enhanced sampling, to construct a comprehensive dataset to ensure
                exhaustive coverage of relevant configurational spaces. Our rigorous
                testing protocols, including torsion scanning, global minimum
                searches, and high-temperature MD simulations across various organic
                molecules, have culminated in an NN model that achieves chemical
                precision commensurate with the highly regarded DFT model, while
                significantly outstripping the accuracy of prevalent semi-empirical
                methods. This study presents a leap forward in the predictive
                modelling of molecular interactions, offering extensive applications
                in drug development and beyond.</jats:p>
                                   """)
            .strip()
            .replace("\n", " "),
            doi="10.26434/chemrxiv-2024-sq8nh",
        ),
        expected_bibtex=textwrap.dedent(r"""
            @Article{Yang_ChemRxiv_2024,
                author =   {Manyi Yang and Duo Zhang and Xinyan Wang and Lingfeng Zhang and Tong
                         Zhu and Han Wang},
                title =    {{Ab initio Accuracy Neural Network Potential for Drug-like Molecules}},
                journal =  {ChemRxiv},
                year =     2024,
                doi =      {10.26434/chemrxiv-2024-sq8nh},
                abstract = {The advent of machine learning (ML) in computational chemistry heralds
                         a transformative approach to one of the quintessential challenges in
                         computer-aided drug design (CADD): the accurate and cost-effective
                         calculation of atomic interactions. By leveraging a neural network
                         (NN) potential, we address this balance and push the boundaries of the
                         NN potential's representational capacity. Our work details the
                         development of a robust general-purpose NN potential, architected on
                         the framework of DPA-2, a deep learning potential with attention,
                         which demonstrates remarkable fidelity in replicating the interatomic
                         potential energy surface for drug-like molecules comprising eight
                         critical chemical elements: H, C, N, O, F, S, Cl, and P. We employed
                         state-of-the-art molecular dynamic techniques, including temperature
                         acceleration and enhanced sampling, to construct a comprehensive
                         dataset to ensure exhaustive coverage of relevant configurational
                         spaces. Our rigorous testing protocols, including torsion scanning,
                         global minimum searches, and high-temperature MD simulations across
                         various organic molecules, have culminated in an NN model that
                         achieves chemical precision commensurate with the highly regarded DFT
                         model, while significantly outstripping the accuracy of prevalent
                         semi-empirical methods. This study presents a leap forward in the
                         predictive modelling of molecular interactions, offering extensive
                         applications in drug development and beyond.},
            }""").strip(),
    ),
]
