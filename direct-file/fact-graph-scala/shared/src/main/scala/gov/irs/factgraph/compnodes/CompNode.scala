package gov.irs.factgraph.compnodes

import gov.irs.factgraph.*
import gov.irs.factgraph.definitions.*
import gov.irs.factgraph.definitions.fact.{CompNodeConfigTrait, LimitConfigTrait}
import gov.irs.factgraph.persisters.Persister
import gov.irs.factgraph.util.Seq.itemsHaveSameRuntimeClass

import scala.collection.mutable
import gov.irs.factgraph.limits.Limit
import transformations.TruncateNameForMeF

trait CompNode:
  type Value

  /** Runtime class of associated value */
  def ValueClass: Class[Value]

  val expr: Expression[Value]
  export expr.{get, getThunk, explain, set, delete, isWritable}

  private[compnodes] def fromExpression(expr: Expression[Value]): CompNode
  private[compnodes] def switch(
      cases: List[(BooleanNode, CompNode)],
  ): CompNode =
    if (!itemsHaveSameRuntimeClass(cases.map(_._2)))
      val caseTypes = cases.map(_._2.getClass.getSimpleName).distinct.mkString(", ")
      throw new UnsupportedOperationException(
        s"cannot switch between nodes of different types: $caseTypes",
      )

    fromExpression(
      Expression.Switch(
        cases.map((b, a) => (b.expr, a.expr.asInstanceOf[Expression[Value]])),
      ),
    )
  private[compnodes] def dependency(path: Path): CompNode = fromExpression(
    Expression.Dependency(path),
  )
  def extract(key: PathItem): Option[CompNode] = None

  def getIntrinsicLimits()(using Factual): Seq[Limit] = Seq.empty

object CompNode:
  private val defaultFactories: Seq[CompNodeFactory] = List(
    // Constant nodes
    BooleanNode.False,
    BooleanNode.True,
    DollarNode,
    IntNode,
    DaysNode,
    LegacyDateNode,
    RationalNode,
    DayNode,
    StringNode,
    TinNode,
    EinNode,
    EmailAddressNode,
    AddressNode,
    BankAccountNode,
    EnumNode,
    MultiEnumNode,
    PhoneNumberNode,

    // Operation nodes
    Add,
    All,
    Any,
    Today,
    AsString,
    AsDecimalString,
    CollectionSize,
    Count,
    Dependency,
    Divide,
    EnumOptionsContains,
    EnumOptionsSize,
    EnumOptionsNode,
    Equal,
    Filter,
    FirstNCollectionItems,
    Find,
    GreaterOf,
    GreaterThan,
    GreaterThanOrEqual,
    IndexOf,
    IsComplete,
    Length,
    LesserOf,
    LessThan,
    LessThanOrEqual,
    Maximum,
    Minimum,
    Multiply,
    Not,
    NotEqual,
    Paste,
    Placeholder,
    Regex,
    Round,
    RoundToInt,
    StepwiseMultiply,
    StripChars,
    Subtract,
    CollectionSum,
    Switch,
    Trim,
    ToUpper,
    TruncateCents,
    TruncateNameForMeF,
    LegacyMin,
    LegacyMax,
    LegacyEquals,
    LegacySum,
    LegacyAnd,
    LegacyOr,
  )

  private val factories = mutable.Map(defaultFactories.map(_.asTuple)*)

  def register(f: CompNodeFactory): Unit = factories.addOne(f.asTuple)

  def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    val factory = factories.getOrElse(
      e.typeName,
      throw new UnsupportedOperationException(
        s"${e.typeName} is not a registered CompNode",
      ),
    )

    factory.fromDerivedConfig(e)

  def getConfigChildNode(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    val children = e.children
      .map(fromDerivedConfig(_))

    children match
      case child :: Nil => child
      case _ =>
        throw new IllegalArgumentException(
          s"<${e.typeName}> must have exactly one child node: $e",
        )

  def getConfigChildNodes(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): Seq[CompNode] =
    val children = e.children
      .map(fromDerivedConfig(_))

    children match
      case Nil =>
        throw new IllegalArgumentException(
          s"<${e.typeName}> must have at least one child node: $e",
        )
      case _ => children.toSeq

  def getConfigChildNode(e: CompNodeConfigTrait, label: String)(using Factual)(using
      FactDictionary,
  ): CompNode =
    val children = e.children
      .filter(x => x.typeName == label)
      .flatMap(_.children)
      .map(fromDerivedConfig(_))

    children match
      case child :: Nil => child
      case _ =>
        throw new IllegalArgumentException(
          s"<${e.typeName}> must have exactly one <$label>: $e",
        )

  def getConfigChildNodes(e: CompNodeConfigTrait, label: String)(using Factual)(using
      FactDictionary,
  ): Seq[CompNode] =
    val children = e.children
      .filter(x => x.typeName == label)
      .flatMap(_.children)
      .map(fromDerivedConfig(_))

    children match
      case Nil =>
        throw new IllegalArgumentException(
          s"<${e.typeName}> must have at least one <$label>: $e",
        )
      case _ => children.toSeq

private object LegacyMin extends CompNodeFactory:
  override val Key: String = "Min"

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    LesserOf.fromDerivedConfig(e)

private object LegacyMax extends CompNodeFactory:
  override val Key: String = "Max"

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    GreaterOf.fromDerivedConfig(e)

private object LegacyEquals extends CompNodeFactory:
  override val Key: String = "Equals"

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    Equal.fromDerivedConfig(e)

private object LegacySum extends CompNodeFactory:
  override val Key: String = "Sum"

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    Add.fromDerivedConfig(e)

private object LegacyAnd extends CompNodeFactory:
  override val Key: String = "And"

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    All.fromDerivedConfig(e)

private object LegacyOr extends CompNodeFactory:
  override val Key: String = "Or"

  override def fromDerivedConfig(e: CompNodeConfigTrait)(using Factual)(using
      FactDictionary,
  ): CompNode =
    Any.fromDerivedConfig(e)
